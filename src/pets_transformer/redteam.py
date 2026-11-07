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

JSON output holds counts and rates only: never truth values, row-map contents or the values of a group.
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

GATE = {"order_attack": 0.05, "news_linkage": 0.0, "person_fingerprint": 0.05, "scorer_linkage_band_aware": 0.01,
        "plain_hash": 0.0}
HOUR = re.compile(r"^\d\d:00$")


def _read(p):
    return pd.read_csv(p, dtype=str)


def _time_column(contract):
    for t, cols in contract["columns"].items():
        for c, rule in cols.items():
            if rule["pet"] == "hour_of_day":
                return t, c
    return None, None


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
    arr = np.full(len(rel), np.datetime64("NaT"), dtype="datetime64[ns]")
    arr[idx] = (t0 + pd.to_timedelta(days.values + offset, unit="D")).values.astype("datetime64[ns]")
    rebuilt = pd.Series(arr, index=rel.index)
    share_all = float((rebuilt.dt.normalize() == pd.to_datetime(orig_dates, errors="coerce").dt.normalize()).mean())
    return {"orderings_tried": tried, "best_ordering": name, "share_rows_date_rebuilt": round(share_all, 4)}, rebuilt


def _age_ok(band, age):
    if not isinstance(band, str):
        return False
    if band.endswith("+"):
        return age >= int(band[:-1])
    m = re.fullmatch(r"(\d+)-(\d+)", band)
    return bool(m) and int(m.group(1)) <= age <= int(m.group(2))


def news_linkage(rel, rebuilt, rec_ids, news, truth_news, truth_rec, time_col, age_col="date_of_birth"):
    rel = rel.assign(_date=rebuilt.dt.strftime("%Y-%m-%d").values, _rec=rec_ids)
    t_news = truth_news.set_index("adv_row_id")["person_id"]
    t_rec = truth_rec.set_index("record_id")["person_id"]
    usable = singled = correct = 0
    for _, n in news.iterrows():
        m = re.search(r"kello (\d{1,2})", str(n.get("text", "")))
        if not m or not isinstance(n.get("event_date"), str):
            continue
        usable += 1
        c = rel[(rel._date == n.event_date) & (rel[time_col] == f"{int(m.group(1)):02d}:00")]
        if isinstance(n.get("sex_mentioned"), str) and "sex" in c:
            c = c[c.sex == n.sex_mentioned]
        if isinstance(n.get("place"), str) and "municipality" in c:
            c = c[c.municipality.isin([n.place, "other"])]
        if isinstance(n.get("age_mentioned"), str) and age_col in c:
            a = int(n.age_mentioned)
            c = c[c[age_col].map(lambda b: _age_ok(b, a))]
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
    d = rel[[pc] + [c for c in fp_cols if c in rel.columns and c != time_col]].fillna("")
    hours = (rel.groupby(pc)[time_col].apply(lambda s: tuple(sorted(s.fillna("")))) if time_col
             else rel.groupby(pc).size().map(lambda n: ("rows", n)))
    static = d.groupby(pc).first()
    sig = static.apply(tuple, axis=1).astype(str) + "|" + hours.astype(str)
    counts = sig.map(sig.value_counts())
    visits = rel.groupby(pc).size()
    return {"applicable": True, "person_column": pc, "fingerprint": [c for c in fp_cols if c in rel.columns],
            "persons": int(len(sig)), "persons_with_2plus_rows": int((visits > 1).sum()),
            "share_persons_unique": round(float((counts == 1).mean()), 4),
            "share_repeat_persons_unique": round(float((counts[visits > 1] == 1).mean()), 4) if (visits > 1).any() else 0.0}


def scorer_linkage_band_aware(rel, rowmap, original, main, rid, truth, specs_path, adversary):
    """Rerun pets-eval's linkage attacker with the age from the release's age column (a band) and no time QI when the
    release keeps only "HH:00" (the attacker cannot place an hour on a date)."""
    from pets_eval import attacks
    specs = [s for s in json.loads(Path(specs_path).read_text())["attacks"] if s["dataset"] == original.name and s["table"] == main]
    hour_only = {c for c in rel.columns if rel[c].astype(str).str.fullmatch(r"\d\d:00|suppressed").mean() > 0.9}
    age_col = "age" if "age" in rel.columns else None
    identity = _read(Path(truth) / f"{original.name}__{main}.csv")
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
        adv = _read(Path(adversary) / f"{sp['adversary']}.csv")
        adv_truth = _read(Path(truth) / f"adversary__{sp['adversary']}.csv")
        if not q_p:
            out.append({"adversary": sp["adversary"], "evaluated": False, "reason": "no QI of this attacker survives in the release"})
            continue
        r = attacks.linkage_attack(adv, adv_truth, rel, rm, identity, qis=q_p, original=orig, record_key=rid,
                                   sensitive=sp.get("sensitive") if sp.get("sensitive") in rel.columns else None)
        keep = ("reidentification_rate", "claim_precision", "n_unique_claims", "n_targets_in_data",
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


def run(protected, original, contract, out, truth=None, adversary=None, label="", specs_path=None):
    protected, original, out = Path(protected), Path(original), Path(out)
    main, time_col = _time_column(contract)
    if main is None:  # no hour-only column: nothing for the order attack to rebuild; red-team the k target table
        main = (contract.get("k_target") or {}).get("table") or next(t for t, s in contract["tables"].items() if s["action"] == "release")
    rid = contract["tables"][main]["record_id"]
    rel = _read(protected / f"{main}.csv")
    rowmap = _read(protected / f"rowmap_{main}.csv")
    rec_ids = rowmap.set_index(rowmap.protected_row.astype(int))["original_record_id"].reindex(range(len(rel))).values
    orig = _read(original / f"{main}.csv").set_index(rid)
    orig_dates = pd.Series(orig[time_col].reindex(rec_ids).values).str[:10] if time_col else None
    joins = {f.stem: _read(f) for f in sorted(protected.glob("*.csv"))
             if f.stem != main and not f.stem.startswith("rowmap_") and f.stem != "plan"}
    if time_col:
        oa, rebuilt = order_attack(rel, orig_dates, main, time_col, joins)
    else:
        oa, rebuilt = {"applicable": False, "why": "no hour-only column in the release", "share_rows_date_rebuilt": 0.0}, None

    news = None
    if time_col and adversary and truth and (Path(adversary) / "news_clips_health.csv").exists():
        news = news_linkage(rel, rebuilt, rec_ids, _read(Path(adversary) / "news_clips_health.csv"),
                            _read(Path(truth) / "adversary__news_clips_health.csv"),
                            _read(Path(truth) / f"{original.name}__{main}.csv"), time_col)
    # a person key: a pseudonym, or a token that repeats within a table (one subject, several rows)
    kcols = (contract.get("k_target") or {}).get("columns") or [c for c in ["date_of_birth", "sex", "municipality", time_col] if c]
    pf_all = []
    for t, cols in contract["columns"].items():
        f = protected / f"{t}.csv"
        if not f.exists():
            continue
        tab = rel if t == main else _read(f)
        keys = [c for c, r in cols.items() if c in tab.columns and (r["pet"] == "pseudonym" or (r["pet"] == "token" and not tab[c].dropna().is_unique))]
        fp = [c for c in tab.columns if c in kcols or (c in cols and cols[c]["pet"] in ("age_band", "top_n_exact_else_other", "hour_of_day"))]
        tc = time_col if t == main and time_col in tab.columns else None
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
        sl = scorer_linkage_band_aware(rel, rowmap, original, main, rid, truth, specs_path, adversary)
    ph = plain_hash(protected, original)

    results = {
        "order_attack": {"metric": "share_rows_date_rebuilt", "value": oa["share_rows_date_rebuilt"], "detail": oa},
        "news_linkage": {"metric": "share_clips_reidentified", "value": news["share_clips_reidentified"] if news else None, "detail": news},
        "person_fingerprint": {"metric": "share_persons_unique", "value": pf["share_persons_unique"], "detail": pf},
        "scorer_linkage_band_aware": {"metric": "worst_reidentification_rate", "value": sl["worst_reidentification_rate"] if sl else None, "detail": sl},
        "plain_hash": {"metric": "worst_share_reversed", "value": ph["worst_share_reversed"], "detail": ph},
    }
    for k, r in results.items():
        r["threshold"] = GATE[k]
        r["pass"] = None if r["value"] is None else bool(r["value"] <= GATE[k])
    passed = all(r["pass"] is not False for r in results.values())
    report = {"release": label or str(protected.name), "table": main, "time_column": time_col,
              "gate": "pass" if passed else "fail",
              "rule": "every attack at or below its threshold; thresholds are our choice, stated here",
              "attacks": results}
    out.mkdir(parents=True, exist_ok=True)
    return report


def write(report, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(report, indent=2) + "\n")
