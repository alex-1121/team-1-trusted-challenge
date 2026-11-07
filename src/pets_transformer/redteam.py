"""Red team: attacks the organisers' scorecard does not run, each with a pass/fail threshold (the release gate).

1. Order attack. The release keeps the hour of arrival only. If the rows can be put back in arrival order (file order,
   a sequential record key, a sequential key in a linked table), a new day starts wherever the hour goes backwards,
   and the dropped date comes back. Measured: share of released rows whose date is rebuilt exactly.
2. News-clip linkage. The shipped news clips name a date, a clock hour, a place, an age and a sex. Matched against the
   release with the dates from the best ordering. Measured: share of clips that single out the right patient.
3. Person fingerprint. A pseudonym column links every row of a person; age band, sex, municipality and the set of
   arrival hours then form a fingerprint. Measured: share of released persons whose fingerprint is unique.
4. The organisers' own linkage attacker, band-aware. pets-eval reads a column named date_of_birth as a date, so an age
   band gives it no age at all, and it reads "HH:00" as today's date, so its time window matches nothing. Its 0.0 on
   an hour-only, banded release is partly an artefact. We rerun the same attacker (pets_eval.attacks.linkage_attack, the
   attack specs in metadata/attack_specs.json) with the age read from the age column and the unmatchable time dropped.
   Measured: worst re-identification rate over the specs, and worst share of targets whose diagnosis is inferred.
5. Plain hashes. Any released value that equals the MD5, SHA-1 or SHA-256 of an original value of the same table is
   reversible by a dictionary attack. Measured: worst share of a released column's values found that way.

Every attack ends as pass, fail or not_applicable with a stated reason (attack_status). `evaluate` is the release
decision: one pure function over results already loaded, which `build` calls before it copies anything.

JSON output holds counts and rates only: never truth values, row-map contents or the values of a group.
"""
import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

from .generalise import SUPPRESSED, age_ok, hours

ATTACKS = ("order_attack", "news_linkage", "person_fingerprint", "scorer_linkage_band_aware", "plain_hash")
HOUR = re.compile(r"^\d\d:00")  # an exact hour or the start of a repair block "03:00 to 05:59"
NO_QI = "no QI of this attacker survives in the release"
LEAK_RISKS = ("direct identifiers retained", "free-text identifier leakage")
ID_ROLES = {"direct_identifier", "technical_identifier", "record_key"}


def _read(p):
    return pd.read_csv(p, dtype=str)


def _time_columns(contract):
    """Every hour-only column of a released table; a withheld table releases nothing to attack."""
    tables = contract.get("tables", {})
    return [(t, c) for t, cols in contract["columns"].items() if tables.get(t, {}).get("action") == "release"
            for c, rule in cols.items() if rule["pet"] == "hour_of_day"]


def _time_column(contract):
    return next(iter(_time_columns(contract)), (None, None))


def rebuild_days(hours):
    """hours in release order -> day index per row; a new day starts when the hour goes backwards."""
    h = pd.to_numeric(hours.where(hours.str.match(HOUR, na=False)).str[:2], errors="coerce").ffill().fillna(0)
    return (h.diff().fillna(0) < 0).cumsum()


def date_hit_rate(days, true_days):
    """Share of rows whose rebuilt day equals the true day, after the single best offset (the attacker needs one anchor)."""
    diff = (true_days.values - days.values)
    if not len(diff):
        return 0.0, 0
    offset = int(pd.Series(diff).mode().iloc[0])
    return float((diff == offset).mean()), offset


def orderings(rel, main, join_tables):
    """Candidate orders an attacker can try: file order, each unique column, first row per key in a linked table."""
    yield "file order", rel.index.to_numpy()
    for c in rel.columns:
        v = rel[c]
        if v.notna().all() and v.nunique() == len(v):
            yield f"sorted by {main}.{c}", v.sort_values(kind="stable").index.to_numpy()
    for t, other in join_tables.items():
        for jc in [c for c in other.columns if c in rel.columns and rel[c].nunique() == len(rel)]:
            pos = pd.Series(rel.index, index=rel[jc])
            for c in other.columns:
                v = other[c]
                if c == jc or not (v.notna().all() and v.nunique() == len(v)):
                    continue
                first = other.sort_values(c, kind="stable").drop_duplicates(jc)[jc]
                idx = pos.reindex(first.values).dropna().astype(int).to_numpy()
                yield f"first {t}.{c} per {jc}", idx


def order_attack(rel, orig_dates, main, time_col, join_tables):
    """orig_dates: true calendar date per released row (from the row map), aligned with rel."""
    t0 = pd.to_datetime(orig_dates, errors="coerce").min()
    if pd.isna(t0):
        return {"applicable": False, "why": "original time column has no dates", "share_rows_date_rebuilt": 0.0}, \
            pd.Series(pd.NaT, index=rel.index, dtype="datetime64[ns]")
    true_days = (pd.to_datetime(orig_dates, errors="coerce") - t0).dt.days.fillna(-10**6).astype(int)
    tried = []
    best = None
    for name, idx in orderings(rel, main, join_tables):
        if len(idx) < 2:
            continue
        days = rebuild_days(rel[time_col].iloc[idx].reset_index(drop=True))
        rate, offset = date_hit_rate(days, true_days.iloc[idx].reset_index(drop=True))
        tried.append({"ordering": name, "rows": int(len(idx)), "share_dates_rebuilt": round(rate, 4)})
        if best is None or rate * len(idx) > best[1] * len(best[2]):
            best = (name, rate, idx, days, offset)
    name, rate, idx, days, offset = best
    arr = np.full(len(rel), np.datetime64("NaT", "ns"), dtype="datetime64[ns]")
    arr[idx] = (t0 + pd.to_timedelta(days.values + offset, unit="D")).values.astype("datetime64[ns]")
    rebuilt = pd.Series(arr, index=rel.index)
    share_all = float((rebuilt.dt.normalize() == pd.to_datetime(orig_dates, errors="coerce").dt.normalize()).mean())
    return {"orderings_tried": tried, "best_ordering": name, "share_rows_date_rebuilt": round(share_all, 4)}, rebuilt


def news_linkage(rel, rebuilt, rec_ids, news, truth_news, truth_rec, time_col, age_col="date_of_birth"):
    """A released row stays a candidate for a clip whenever its values can stand for the clip's facts: an hour block
    holding the clip's hour, a band holding the age, "other" for a place the release does not show, or suppressed."""
    rel = rel.assign(_date=rebuilt.dt.strftime("%Y-%m-%d").values, _rec=rec_ids)
    hour_sets = rel[time_col].map(hours)
    shown = set(rel["municipality"].dropna()) - {"other", SUPPRESSED} if "municipality" in rel else set()
    t_news = truth_news.set_index("adv_row_id")["person_id"]
    t_rec = truth_rec.set_index("record_id")["person_id"]
    usable = singled = correct = 0
    for _, n in news.iterrows():
        m = re.search(r"kello (\d{1,2})", str(n.get("text", "")))
        if not m or not isinstance(n.get("event_date"), str):
            continue
        usable += 1
        h = int(m.group(1))
        c = rel[(rel._date == n.event_date) & hour_sets.map(lambda s: h in s)]
        if isinstance(n.get("sex_mentioned"), str) and "sex" in c:
            c = c[c.sex.isin([n.sex_mentioned, SUPPRESSED])]
        if isinstance(n.get("place"), str) and "municipality" in c:
            ok = [n.place, SUPPRESSED] + (["other"] if n.place not in shown else [])
            c = c[c.municipality.isin(ok)]
        if isinstance(n.get("age_mentioned"), str) and age_col in c:
            a = int(n.age_mentioned)
            c = c[c[age_col].map(lambda b: age_ok(b, a))]
        if len(c) == 1:
            singled += 1
            correct += int(t_rec.get(c._rec.iloc[0]) == t_news.get(n.adv_row_id))
    return {"clips": int(len(news)), "clips_with_date_and_hour": usable, "singled_out": singled, "correct": correct,
            "share_clips_reidentified": round(correct / len(news), 4) if len(news) else 0.0}


def person_fingerprint(rel, person_cols, fp_cols, time_col):
    if not person_cols:
        return {"applicable": False, "why": "no person key released (no pseudonym column)", "share_persons_unique": 0.0}
    pc = person_cols[0]
    rel = rel[rel[pc].notna()]  # rows without a person key link to nobody
    # a fingerprint column is a fact about the person: constant over a person's rows (age band, place). A value that
    # changes on every row (the timestamp of each meter reading) is not something an outsider knows about a person;
    # only the hour-only time column enters, as the set of a person's hours (visits seen in the news).
    static_cols = [c for c in fp_cols if c in rel.columns and c != time_col
                   and rel.groupby(pc)[c].nunique(dropna=False).le(1).mean() >= 0.9]
    if not static_cols and not time_col:
        return {"applicable": False, "person_column": pc, "why": "person key released, but no per-person quasi-identifier in this table",
                "share_persons_unique": 0.0}
    d = rel[[pc] + static_cols].fillna("")
    hours = (rel.groupby(pc)[time_col].apply(lambda s: tuple(sorted(s.fillna("")))) if time_col
             else rel.groupby(pc).size().map(lambda n: ("rows", n)))
    static = d.groupby(pc).first()
    sig = static.apply(tuple, axis=1).astype(str) + "|" + hours.astype(str)
    counts = sig.map(sig.value_counts())
    visits = rel.groupby(pc).size()
    return {"applicable": True, "person_column": pc, "fingerprint": static_cols + ([f"set of {time_col}"] if time_col else []),
            "persons": int(len(sig)), "persons_with_2plus_rows": int((visits > 1).sum()),
            "share_persons_unique": round(float((counts == 1).mean()), 4),
            "share_repeat_persons_unique": round(float((counts[visits > 1] == 1).mean()), 4) if (visits > 1).any() else 0.0}


def scorer_linkage_band_aware(rel, rowmap, original, main, rid, truth, specs_path, adversary):
    """Rerun pets-eval's linkage attacker with the age from the release's age column (a band) and no time QI when the
    release keeps only "HH:00" (the attacker cannot place an hour on a date)."""
    from pets_eval import attacks
    specs = [s for s in json.loads(Path(specs_path).read_text())["attacks"] if s["dataset"] == original.name and s["table"] == main]
    if not specs:
        return {"specs": [], "worst_reidentification_rate": 0.0}
    hour_only = {c for c in rel.columns if rel[c].astype(str).str.fullmatch(r"\d\d:00|\d\d:00 to \d\d:59|suppressed").mean() > 0.9}
    age_col = "age" if "age" in rel.columns else None
    identity_file = Path(truth) / f"{original.name}__{main}.csv"
    identity = _read(identity_file) if identity_file.exists() else None
    orig = _read(original / f"{main}.csv")
    rm = rowmap.assign(protected_row=rowmap.protected_row.astype(int))
    out = []
    for sp in specs:
        qis = []
        for q in sp["qis"]:
            q = dict(q)
            if q["kind"] == "age" and age_col:
                q["protected"] = [age_col]
            if q["kind"] == "time" and any(c in hour_only for c in q["protected"]):
                continue
            qis.append(q)
        q_p = attacks.qis_from_spec(qis, rel.columns)
        if not q_p:
            out.append({"adversary": sp["adversary"], "evaluated": False, "reason": NO_QI})
            continue
        adv_file, adv_truth_file = Path(adversary) / f"{sp['adversary']}.csv", Path(truth) / f"adversary__{sp['adversary']}.csv"
        gone = [f.name for f in (adv_file, adv_truth_file, identity_file) if not f.exists()]
        if gone:
            out.append({"adversary": sp["adversary"], "evaluated": False, "reason": "input files missing: " + ", ".join(gone)})
            continue
        r = attacks.linkage_attack(_read(adv_file), _read(adv_truth_file), rel, rm, identity, qis=q_p, original=orig, record_key=rid,
                                   sensitive=sp.get("sensitive") if sp.get("sensitive") in rel.columns else None)
        keep = ("evaluated", "reason", "reidentification_rate", "claim_precision", "n_unique_claims", "n_targets_in_data",
                "share_targets_in_candidate_set_le5", "median_candidate_set", "attribute_inference")
        out.append({"adversary": sp["adversary"], "qis_used": [{"kind": q.kind, "protected": list(q.prot)} for q in q_p],
                    **{k: r.get(k) for k in keep if k in r}})
    worst = max([o.get("reidentification_rate") or 0.0 for o in out] or [0.0])
    return {"specs": out, "worst_reidentification_rate": worst}


def plain_hash(protected, original, max_values=20000):
    import hashlib
    worst, found = 0.0, []
    for f in sorted(protected.glob("*.csv")):
        if f.stem.startswith("rowmap_") or f.stem == "plan" or not (original / f.name).exists():
            continue
        rel, orig = _read(f), _read(original / f.name)
        vals = [v for v in pd.unique(orig.to_numpy().ravel()) if isinstance(v, str)][:500000]
        digests = set()
        for v in vals:
            b = v.encode()
            digests |= {hashlib.md5(b).hexdigest(), hashlib.sha1(b).hexdigest(), hashlib.sha256(b).hexdigest()}
        for c in rel.columns:
            s = rel[c].dropna().astype(str).str.strip().str.lower()
            s = s[s.str.fullmatch(r"[0-9a-f]{32}|[0-9a-f]{40}|[0-9a-f]{64}")].head(max_values)
            if len(s):
                share = float(s.isin(digests).mean())
                found.append({"table": f.stem, "column": c, "share_reversed": round(share, 4)})
                worst = max(worst, share)
    return {"hash_like_columns": found, "worst_share_reversed": round(worst, 4)}


def _number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def attack_status(name, attack, time_col, thresholds):
    """(status, reason) from an attack's stored fields, so a committed report without a status reads the same way.
    not_applicable only when the release gives the attack nothing to work on; an attack that should have run and
    could not is a fail, whatever value it left behind."""
    value, d = attack.get("value"), attack.get("detail") or {}
    if name in ("order_attack", "news_linkage") and not time_col:
        return "not_applicable", "no hour-only column in the release"
    idle = [x for x in d.get("columns_checked", [d]) if x.get("applicable") is False]
    if name == "order_attack" and idle:
        return "fail", f"could not run: {idle[0].get('why')}"
    if name == "news_linkage":
        if d.get("applicable") is False:
            return "not_applicable", d.get("why")
        if not d.get("clips_with_date_and_hour"):
            return "fail", "could not run: the release has an hour column, but the news clips or their truth files are missing or hold no clip with a date and an hour"
    if name == "person_fingerprint" and not any(t.get("applicable") for t in d.get("tables_checked", [])):
        return ("not_applicable", d["why"]) if d.get("why") else ("fail", "did not run")
    if name == "scorer_linkage_band_aware":
        if d.get("specs") is None:
            return "fail", "could not run: attack specs, truth or adversary folder not available"
        specs = d["specs"]
        broken = [s for s in specs if s.get("reason") != NO_QI and not _number(s.get("reidentification_rate"))]
        if broken:
            return "fail", "could not run: " + "; ".join(f"{s.get('adversary')}: {s.get('reason', 'no rate measured')}" for s in broken)
        if not any(_number(s.get("reidentification_rate")) for s in specs):
            return "not_applicable", NO_QI if specs else "no attack spec targets a released table"
    if not _number(value):
        return "fail", "did not run"
    return ("pass", None) if value <= thresholds[name] else ("fail", f"{value} over the threshold {thresholds[name]}")


def attack_failures(attacks, time_col, thresholds):
    """One reason per attack that failed; an attack missing from the report is a failure."""
    out = []
    for name in ATTACKS:
        status, why = attack_status(name, attacks[name], time_col, thresholds) if name in attacks else ("fail", "did not run")
        if status == "fail":
            out.append(f"attack {name}: {why}")
    return out


def shown(attack):
    """An attack's result for human eyes: a measurement of nothing never reads as 0.0."""
    if attack["status"] == "not_applicable":
        return "not applicable"
    return "did not run" if attack["value"] is None else attack["value"]


def expected_files(contract):
    """The release, from the contract and never from a folder listing: each released table and its row map."""
    return sorted(f for t, s in contract["tables"].items() if s["action"] == "release" for f in (f"{t}.csv", f"rowmap_{t}.csv"))


def _at(d, *path):
    for p in path:
        d = d.get(p) if isinstance(d, dict) else None
    return d


def _under(what, value, floor):
    """The reason value fails a floor, or None when it clears it; a null or NaN is not a measurement."""
    if not _number(value):
        return f"{what} not measured"
    return f"{what} {value} under {floor}" if value < floor else None


def evaluate(policy, contract, report, card, check_results, scan, csv_files, required_tasks):
    """The release decision. Pure: it sees only what this run produced, already loaded, and every limit is the policy's.
    report: redteam.run's output. card: the scorecard. check_results: file name -> object from this run's checks.
    scan: the structured identifier scan, None if it did not run. csv_files: every CSV under the protected folder,
    relative to it. required_tasks: the scenario definition's list; a policy can add tasks to it, never remove one.
    Returns gate, reasons and utility_check."""
    reasons = attack_failures(report.get("attacks") or {}, report.get("time_column"), policy["attack_thresholds"])
    for t, spec in contract["tables"].items():
        if spec["action"] == "release" and _at(card, "tables", t, "status") != "released":
            reasons.append(f"scorecard: table {t} has status {_at(card, 'tables', t, 'status')}")

    kt, k, l = contract.get("k_target"), policy["k_min"], policy["l_min"] or 1
    if bool(kt) != (k is not None):
        reasons.append("policy: k_min and the contract's k target do not match")
    elif kt:
        need = ["informed_attacker.json"]
        need += ["l_diversity.json"] if kt.get("sensitive") or l > 1 else []
        need += ["joined_k.json"] if kt.get("join_flags") else []
        reasons += [f"check did not run: {n}" for n in need if n not in check_results]
        reasons.append(_under(f"k: scorer min k of {kt['table']}", _at(card, "tables", kt["table"], "k_anonymity", "min_k"), k))
        if "joined_k.json" in check_results:  # the top-level result counts the exact diagnosis code; per_join alone holds every join
            jk = check_results["joined_k.json"]
            for t, j in (jk.get("per_join") or {"the joined tables": jk}).items():
                reasons.append(_under(f"joined k: min k with {t}", _at(j, "for_comparison_k_columns_only", "min_k"), k))
        if l > 1 and "l_diversity.json" in check_results:
            reasons.append(_under("l: fewest distinct values in a group", _at(check_results["l_diversity.json"], "result", "worst_group", "distinct"), l))

    scores = {u.get("id"): u.get("score") for u in card.get("utility") or []}
    utility_floor = policy["utility_floor"]
    tasks = {t: scores.get(t) for t in [*(required_tasks or []), *policy["required_tasks"]]}
    short = {t: _under(f"required task {t}", v, utility_floor) for t, v in tasks.items()}
    short = {t: why for t, why in short.items() if why}
    reasons += [f"utility: {why}" for why in short.values()]
    if not required_tasks:
        reasons.append("utility: the scenario definition names no required task")

    if not isinstance(_at(scan, "totals"), dict) or not _at(scan, "n_files_scanned"):
        reasons.append("identifier scan: did not run")
    elif scan["totals"]:
        reasons.append("identifier scan: found " + ", ".join(f"{k} {v}" for k, v in sorted(scan["totals"].items())))
    for name, v in (card.get("risk_components") or {}).items():
        if name.endswith(LEAK_RISKS) and not (_number(v) and v <= 0):
            reasons.append(f"scorer risk: {name} is {v}")

    expected = set(expected_files(contract))
    stray = sorted(set(csv_files) - expected - {"plan.csv"})  # plan.csv is protect's own record, never copied
    reasons += [f"files: unexpected CSV {f}" for f in stray]
    reasons += [f"files: expected CSV missing {f}" for f in sorted(expected - set(csv_files))]

    reasons = [r for r in reasons if r]
    return {"gate": "fail" if reasons else "pass", "reasons": reasons,
            "rule": "every attack at or below its threshold or not applicable with a reason; k, joined k and l at the policy's minimum; "
                    "every check the contract needs has run; every required task at the floor; no identifier found; "
                    "only the contract's files in the release; every limit comes from the signed policy",
            "utility_check": {"rule": f"every required task scores at least {utility_floor}", "scores": tasks,
                              "pass": bool(tasks) and not short, "below_floor": {t: tasks[t] for t in short}}}


def run(protected, original, contract, out, thresholds, truth=None, adversary=None, label="", specs_path=None):
    protected, original, out = Path(protected), Path(original), Path(out)
    hour_cols = _time_columns(contract)
    main, time_col = hour_cols[0] if hour_cols else (None, None)
    if main is None:  # no hour-only column: nothing for the order attack to rebuild; red-team the k target table
        main = (contract.get("k_target") or {}).get("table") or next(t for t, s in contract["tables"].items() if s["action"] == "release")
    rid = contract["tables"][main]["record_id"]
    rel = _read(protected / f"{main}.csv")
    rowmap = _read(protected / f"rowmap_{main}.csv")
    rec_ids = rowmap.set_index(rowmap.protected_row.astype(int))["original_record_id"].reindex(range(len(rel))).values

    def released(t):  # a released table, and the original record id of each of its rows
        if t == main:
            return rel, rec_ids
        tab, rm = _read(protected / f"{t}.csv"), _read(protected / f"rowmap_{t}.csv")
        return tab, rm.set_index(rm.protected_row.astype(int))["original_record_id"].reindex(range(len(tab))).values

    oas, rebuilt = [], {}
    for t, c in hour_cols:  # every hour-only column, each against its own table's order
        tab, recs = released(t)
        orig_dates = pd.Series(_read(original / f"{t}.csv").set_index(contract["tables"][t]["record_id"])[c].reindex(recs).values).str[:10]
        joins = {f.stem: _read(f) for f in sorted(protected.glob("*.csv")) if f.stem not in (t, "plan") and not f.stem.startswith("rowmap_")}
        a, rebuilt[(t, c)] = order_attack(tab, orig_dates, t, c, joins)
        oas.append({"table": t, "column": c, **a})
    if oas:
        oa = {**max(oas, key=lambda a: a["share_rows_date_rebuilt"]),
              "columns_checked": [{k: a.get(k) for k in ("table", "column", "applicable", "why", "share_rows_date_rebuilt")} for a in oas]}
    else:
        oa = {"applicable": False, "why": "no hour-only column in the release", "share_rows_date_rebuilt": 0.0}

    news = None
    if hour_cols and original.name != "health":
        news = {"applicable": False, "why": "the news clips describe health visits, and this release holds other data"}
    elif hour_cols and adversary and truth:
        runs = []
        for t, c in hour_cols:
            need = [Path(adversary) / "news_clips_health.csv", Path(truth) / "adversary__news_clips_health.csv", Path(truth) / f"{original.name}__{t}.csv"]
            if not all(f.exists() for f in need):
                runs = None  # an hour column the clips cannot be matched against: the attack did not run
                break
            tab, recs = released(t)
            runs.append({"table": t, "column": c, **news_linkage(tab, rebuilt[(t, c)], recs, *map(_read, need), c)})
        if runs:
            news = {**max(runs, key=lambda r: r["share_clips_reidentified"]),
                    "columns_checked": [{k: r[k] for k in ("table", "column", "clips_with_date_and_hour", "share_clips_reidentified")} for r in runs]}
    # a person key: a pseudonym, or a token or an identifier kept as it is that repeats within a table (one subject,
    # several rows). The PET and the detected role come from protect's plan.csv, else from the contract's named rules.
    plan = _read(protected / "plan.csv").fillna("") if (protected / "plan.csv").exists() else None
    resolved = {} if plan is None else {(r.table, r.column): (r.role, r.pet) for r in plan.itertuples() if not r.pet.startswith("repair:")}
    kcols = (contract.get("k_target") or {}).get("columns") or [c for c in ["date_of_birth", "sex", "municipality", time_col] if c]
    pf_all = []
    for t in [t for t, s in contract["tables"].items() if s["action"] == "release"]:
        f = protected / f"{t}.csv"
        if not f.exists():
            continue
        tab = rel if t == main else _read(f)
        rule = {c: resolved.get((t, c), ("", contract["columns"].get(t, {}).get(c, {}).get("pet", ""))) for c in tab.columns}
        keys = [c for c, (role, pet) in rule.items() if pet == "pseudonym" or (
            (pet == "token" or (pet == "keep" and role in ID_ROLES)) and not tab[c].dropna().is_unique)]
        fp = [c for c in tab.columns if c in kcols or rule[c][1] in ("age_band", "top_n_exact_else_other", "hour_of_day")]
        tc = next((c for tt, c in hour_cols if tt == t), None)
        if keys and (fp or tc):
            r = person_fingerprint(tab, keys[:1], fp, tc)
            pf_all.append({"table": t, **r})
        elif keys:
            pf_all.append({"table": t, "applicable": False, "person_column": keys[0],
                           "why": "person key released, but no quasi-identifier in this table to fingerprint", "share_persons_unique": 0.0})
    pf = max(pf_all, key=lambda r: r["share_persons_unique"]) if pf_all else {
        "applicable": False, "why": "no person key released (no pseudonym, no repeating token)", "share_persons_unique": 0.0}
    pf = {**pf, "tables_checked": pf_all}

    sl = None
    if truth and adversary and specs_path and Path(specs_path).exists():
        # every released table an attack spec targets, not only the main one
        sl = {"specs": [], "worst_reidentification_rate": 0.0}
        for t in [t for t, s in contract["tables"].items() if s["action"] == "release" and (protected / f"{t}.csv").exists()]:
            tr = rel if t == main else _read(protected / f"{t}.csv")
            rm = rowmap if t == main else _read(protected / f"rowmap_{t}.csv")
            r = scorer_linkage_band_aware(tr, rm, original, t, contract["tables"][t]["record_id"], truth, specs_path, adversary)
            sl["specs"] += [{"table": t, **x} for x in r["specs"]]
            sl["worst_reidentification_rate"] = max(sl["worst_reidentification_rate"], r["worst_reidentification_rate"])
    ph = plain_hash(protected, original)

    results = {
        "order_attack": {"metric": "share_rows_date_rebuilt", "value": oa["share_rows_date_rebuilt"], "detail": oa},
        "news_linkage": {"metric": "share_clips_reidentified", "value": (news or {}).get("share_clips_reidentified"), "detail": news},
        "person_fingerprint": {"metric": "share_persons_unique", "value": pf["share_persons_unique"], "detail": pf},
        "scorer_linkage_band_aware": {"metric": "worst_reidentification_rate", "value": sl["worst_reidentification_rate"] if sl else None, "detail": sl},
        "plain_hash": {"metric": "worst_share_reversed", "value": ph["worst_share_reversed"], "detail": ph},
    }
    for k, r in results.items():
        r["threshold"] = thresholds[k]
        r["status"], r["reason"] = attack_status(k, r, time_col, thresholds)
        r["pass"] = {"pass": True, "fail": False}.get(r["status"])
        if r["status"] == "not_applicable":
            r["value"] = None  # the 0.0 an idle attack returns is not a measurement
    report = {"release": label or str(protected.name), "table": main, "time_column": time_col, "time_columns": [list(x) for x in hour_cols],
              "gate": "fail" if attack_failures(results, time_col, thresholds) else "pass",
              "rule": "every attack at or below its threshold or not applicable with a reason; thresholds come from the policy",
              "attacks": results}
    out.mkdir(parents=True, exist_ok=True)
    return report


def write(report, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(report, indent=2) + "\n")
