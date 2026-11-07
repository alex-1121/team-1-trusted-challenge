"""Select: write the scenario contract from the detected labels and the scenario's required tasks.

Every column gets a menu of candidate PETs for its detected role and subtype (for a timestamp: drop, month, ISO week,
hour of day, date, date and hour; for a birth date: drop, 20-year band, 10-year band; for a place: drop, eight most
common else "other", exact; for coordinates: drop, 2 decimals (about 1 km), 3 decimals (about 100 m); for an
identifier code: drop, keyed token; for a direct identifier or free text: drop only). The order of a menu means
nothing: every candidate is measured and a stated rule decides.

1. Reference: every column at its finest candidate, quasi-identifiers exact, direct identifiers dropped.
   The scenario's required tasks are scored on it with the organisers' utility code (run_utility). That is the
   most utility any candidate can keep.
2. Tables first: a table is withheld when no required task loses more than TOL without it.
3. Columns, riskiest role first (quasi-identifiers, then identifier codes, sensitive values, plain values): every
   candidate gets its utility scores (with the choices already made in place) and its risk (see risk(): the share of
   the table's rows whose knowable values are shared by fewer than K rows, before the k repair, with every column
   not judged yet dropped). Rule: among the candidates that keep every required task within TOL of the reference
   and have risk below RISK_LINE, the highest mean utility; ties within 1e-9: lower risk, then fewer distinct
   values in the protected column (drop counts as 0), then the candidate name in alphabetical order. If none is below the line: the feasible one with the lowest risk, and the
   reason says the line was not met. If none is feasible: the best scores, and the reason says so.
   Before the rule, a candidate other than drop is set aside unless it raises at least one required task by
   MIN_GAIN over drop (per task, not the mean); if none is left, drop is chosen. The repair pass applies the same.
   The gain test applies only when drop is itself feasible; a drop that breaks a required task is no option.
4. k target for the main table (the one with most quasi-identifiers in the reference): the kept quasi-identifiers,
   l-diversity on a kept diagnosis code, join flags for tables joined on its key, and a repair ladder built from
   the chosen PETs.
5. After the repair: step 3 judges a column before the k repair, and a quasi-identifier kept too fine makes the
   repair coarsen or suppress most rows. So every kept quasi-identifier is judged again by the same rule, where
   feasible means a mean score on the repaired release (k target rebuilt each time) no worse than the current one.
   Rounds repeat until nothing moves (at most 3).
6. Reported, not used to decide: the risk after the k repair on each table's knowable columns, and under `fitness`
   the same count when the attacker knows every kept value except keyed tokens and free text.

Every column rule states its reason with the measured scores, the risk and the line. Neither the detector nor the
menus read column names; names appear only as keys of the written contract.
"""
import json
from pathlib import Path

import pandas as pd
from pets_eval import io as pio
from pets_eval.scorecard import run_utility

from . import detect, protect
from . import repair as rp

TOL = 0.05
RISK_LINE = 0.05  # policy number set by the team, printed in every reason
MIN_GAIN = 0.01  # a candidate other than drop must raise one required task by this much over drop (Arda, 2026-11-07)
K = 5
CATEGORY_MAX = 20  # a plain category with more distinct values than this is not assumed known to an attacker
KEYED = {"token", "pseudonym"}
KNOWABLE_RULE = ("a kept column the detector labels quasi_identifier (any subtype), or a kept non_sensitive column of"
                 f" subtype CATEGORY with at most {CATEGORY_MAX} distinct values; sensitive attributes, dropped columns,"
                 " keyed tokens and free text are never knowable")
RISK_ORDER = {"quasi_identifier": 0, "technical_identifier": 1, "sensitive_attribute": 2, "free_text": 3,
              "non_sensitive": 4, "record_key": 5, "direct_identifier": 6}
PLACE = {"MUNICIPALITY", "LOCATION_NAME"}
TIME = {"TIMESTAMP", "DATE"}
DROP = {"pet": "drop"}
TOKEN = {"pet": "token", "params": {"prefix": "T"}}


def candidates(role, subtype):
    """The menu of (rule, short name) for a role and subtype. The list order is for people reading it; the
    selector never reads it."""
    if role in ("direct_identifier", "free_text"):
        return [(DROP, "drop")]
    if role in ("record_key", "technical_identifier"):
        return [(DROP, "drop"), (TOKEN, "keyed token")]
    if role == "quasi_identifier":
        if subtype == "BIRTH_DATE":
            return [(DROP, "drop"), ({"pet": "age_band", "params": {"width": 20, "also_as": ["age"]}}, "20-year age band"),
                    ({"pet": "age_band", "params": {"width": 10, "also_as": ["age"]}}, "10-year age band")]
        if subtype in TIME:
            return [(DROP, "drop"), ({"pet": "month"}, "month"), ({"pet": "week"}, "ISO week"),
                    ({"pet": "hour_of_day"}, "hour of day"), ({"pet": "day"}, "date"),
                    ({"pet": "date_hour"}, "date and hour")]
        if subtype in PLACE:
            return [(DROP, "drop"), ({"pet": "top_n_exact_else_other", "params": {"n": 8}}, "8 most common, rest other"),
                    ({"pet": "keep"}, "exact")]
        if subtype == "GPS_COORDINATE":
            return [(DROP, "drop"), ({"pet": "round_decimals", "params": {"decimals": 2}}, "2-decimal grid (about 1 km)"),
                    ({"pet": "round_decimals", "params": {"decimals": 3}}, "3-decimal grid (about 100 m)")]
        if subtype == "POSTCODE":
            return [(DROP, "drop"), ({"pet": "prefix", "params": {"n": 2}}, "2-digit postcode area"),
                    ({"pet": "prefix", "params": {"n": 3}}, "3-digit postcode area")]
        return [(DROP, "drop"), ({"pet": "keep"}, "exact")]
    return [(DROP, "drop"), ({"pet": "keep"}, "kept")]


def _scores(util, required):
    return {u["id"]: (u["score"] or 0.0) for u in util if u["id"] in required}


def _release(contract, orig, key, labels):
    prot = {}
    for t, spec in contract["tables"].items():
        if spec["action"] != "release":
            continue
        roles = dict(labels[labels.table == t][["column", "privacy_role"]].itertuples(index=False))
        prot[t], _, _ = protect.protect_table(t, orig[t], contract, key, roles)
    return prot


def _fmt(s):
    return ", ".join(f"{k} {v:.4f}" for k, v in s.items())


def _mean(sc):
    return sum(sc.values()) / max(len(sc), 1)


def _released_name(col, rule):
    return rule.get("params", {}).get("as", col) if rule["pet"] == "duration" else col


def _share(frame, cols, k=K):
    """Share of rows whose combination of values over cols is shared by fewer than k rows (0.0 on no columns)."""
    if not cols or not len(frame):
        return 0.0
    h = pd.util.hash_pandas_object(frame[cols].astype(str), index=False)
    return float((h.map(h.value_counts()) < k).mean())


def risk(frame, table, contract, labels, k=K):
    """(share, knowable columns): the share of the released frame's rows whose combination of knowable values is
    shared by fewer than k rows. Knowable: a kept column the detector labels quasi_identifier (any subtype, never
    removed by a dtype test), or a kept non_sensitive column of subtype CATEGORY with at most CATEGORY_MAX distinct
    values. Sensitive attributes are the target, never the key; dropped columns, keyed tokens and free text are out.
    No catalogue file and no attacker file is read. The list of columns is returned so the choice can be audited."""
    lab = labels[labels.table == table].set_index("column")
    cols = []
    for col, rule in contract["columns"].get(table, {}).items():
        name = _released_name(col, rule)
        if rule["pet"] == "drop" or rule["pet"] in KEYED or col not in lab.index or name not in frame.columns:
            continue
        role, sub = lab.at[col, "privacy_role"], lab.at[col, "subtype"]
        if role == "quasi_identifier" or (role == "non_sensitive" and sub == "CATEGORY"
                                          and frame[name].nunique() <= CATEGORY_MAX):
            cols.append(name)
    return _share(frame, cols, k), cols


def _fitness(frame, table, contract, labels, k=K):
    """(share, columns) when the attacker knows every kept value of the frame except keyed tokens and free text."""
    spec = contract["columns"].get(table, {})
    lab = labels[labels.table == table].set_index("column")
    cols = []
    for name in frame.columns:
        src = name if name in spec else next((s for s, r in spec.items() if name in r.get("params", {}).get("also_as", [])
                                              or _released_name(s, r) == name), None)
        if src is not None and (spec[src]["pet"] in KEYED
                                or (src in lab.index and lab.at[src, "privacy_role"] == "free_text")):
            continue
        cols.append(name)
    return _share(frame, cols, k), cols


def _decide(tried):
    """tried: dicts with candidate, scores, ok, risk, distinct. Returns (entry, why), why one of line, line not met,
    fallback, no gain. A candidate other than drop competes only if it raises at least one required task by MIN_GAIN
    over drop (per task, not the mean); each entry gets its gain_over_drop. The gain test applies only when drop is
    itself feasible: a drop that breaks a required task is no option, so the normal rule picks. Ties: lower risk, then fewer distinct
    values (so a tie never keeps a finer value), then name. Only measured numbers and the candidate name decide; the
    menu position never does."""
    drop = next((x for x in tried if x["candidate"] == "drop"), None)
    for x in tried if drop is not None else ():
        x["gain_over_drop"] = None if x is drop else max((v - drop["scores"].get(k, 0.0) for k, v in x["scores"].items()), default=0.0)
    if drop is not None and drop["ok"]:
        earned = [x for x in tried if x is not drop and x["gain_over_drop"] >= MIN_GAIN - 1e-12]
        if len(tried) > 1 and not earned:
            return drop, "no gain"
        tried = [drop, *earned]
    feasible = [x for x in tried if x["ok"]]
    under = [x for x in feasible if x["risk"] < RISK_LINE]
    if under:
        top = max(_mean(x["scores"]) for x in under)
        return min((x for x in under if _mean(x["scores"]) >= top - 1e-9),
                   key=lambda x: (x["risk"], x["distinct"], x["candidate"])), "line"
    if feasible:
        return min(feasible, key=lambda x: (x["risk"], -_mean(x["scores"]), x["distinct"], x["candidate"])), "line not met"
    return min(tried, key=lambda x: (-min(x["scores"].values(), default=0.0), -sum(x["scores"].values()),
                                     x["risk"], x["distinct"], x["candidate"])), "fallback"


def _tried_text(tried, ok_word="within", bad_word="outside", against=f"{TOL}"):
    return "; ".join(f"{x['candidate']}: {ok_word if x['ok'] else bad_word} {against} (utility {_fmt(x['scores'])}; risk {x['risk']:.4f}"
                     + (f"; gain over drop {x['gain_over_drop']:.4f}" if x.get("gain_over_drop") is not None else "") + ")"
                     for x in tried)


def _chosen_text(name, entry, why, repaired=False, tried=()):
    line = "met" if entry["risk"] < RISK_LINE else "not met"
    where = "on the repaired release " if repaired else ""
    feasible = "no worse than the current choice" if repaired else f"within {TOL} of the reference"
    text = {"line": f"highest mean utility {where}among the candidates {feasible} and under the risk line {RISK_LINE}",
            "line not met": f"lowest risk among the candidates {feasible}; the risk line {RISK_LINE} was not met",
            "fallback": f"no candidate stayed within the tolerance, so the best scores were taken; risk line {RISK_LINE} {line}",
            "no gain": f"no candidate improves a required task by at least {MIN_GAIN} over drop; risk line {RISK_LINE} {line}"}[why]
    return (f"Chosen: {name} (risk {entry['risk']:.4f}), {text} (a candidate other than drop must raise a required task"
            f" by at least {MIN_GAIN} over drop; ties: lower risk, then fewer distinct values, then name)."
            + ((" Drop lowers the mean task score on the repaired release, so the gain rule does not apply." if repaired
                else " Drop breaks a required task, so the gain rule does not apply.") if any(x["candidate"] == "drop" and not x["ok"] for x in tried) else ""))


def select(original, scenario_id, root, labels=None, key=b"s" * 32, log=print, scen=None, utility_fn=None):
    """utility_fn(domain, orig, prot, scen) -> list of task dicts; default the organisers' run_utility."""
    original, root = Path(original), Path(root)
    scen = scen or pio.get_scenario(scenario_id, root)
    required = scen["utility_requirements"]
    utility_fn = utility_fn or run_utility
    orig = pio.load_tables(original)
    labels = detect.detect_dataset(original, original.name) if labels is None else labels
    domain = original.name

    c = {"scenario": scenario_id, "dataset": domain, "generated_by": "pets_transformer.selector", "tolerance": TOL,
         "risk_line": RISK_LINE, "recipient": scen["recipient"], "purpose": scen["purpose"], "trust_level": scen["trust_level"],
         "threat_model": scen["threat_model"], "required_tasks": required, "tables": {}, "columns": {}, "roles": {}}
    info = {}
    for t, df in orig.items():
        lab = labels[labels.table == t].set_index("column")
        keys = [col for col in df.columns if col in lab.index and lab.at[col, "privacy_role"] == "record_key"]
        rid = keys[0] if keys else next((col for col in df.columns if df[col].is_unique), df.columns[0])
        c["tables"][t] = {"action": "release", "record_id": rid, "reason": "needed by a required task"}
        c["columns"][t] = {}
        for col in df.columns:
            role, sub = (lab.at[col, "privacy_role"], lab.at[col, "subtype"]) if col in lab.index else ("non_sensitive", "")
            ladder = candidates(role, sub)
            # the reference holds the finest candidate: a quasi-identifier exact, any other column its one
            # candidate that is not drop (drop when there is none)
            ref = {"pet": "keep"} if role == "quasi_identifier" else next((r for r, _ in ladder if r["pet"] != "drop"), DROP)
            c["columns"][t][col] = {**ref, "reason": "pending"}
            info[(t, col)] = {"role": role, "subtype": sub, "ladder": ladder, "tried": []}
        # a column the contract does not name (a new column in a later export) is dropped unless it is a plain value
        c["roles"][t] = {r: {**(DROP if r in ("quasi_identifier", "direct_identifier", "free_text", "technical_identifier")
                                else {"pet": "token", "params": {"prefix": "T"}} if r == "record_key" else {"pet": "keep"}),
                             "reason": f"default for a {r.replace('_', ' ')} the contract does not name"} for r in RISK_ORDER}

    def score_now():
        return _scores(utility_fn(domain, orig, _release(c, orig, key, labels), scen), required)

    ref = score_now()
    log(f"reference (quasi-identifiers exact): {_fmt(ref)}")

    def ok(new):
        return all(new[k] >= ref[k] - TOL for k in ref)

    trail = []
    for t in list(orig):
        c["tables"][t]["action"] = "withhold"
        new = score_now()
        if ok(new):
            c["tables"][t]["reason"] = f"Withheld: without it every required task stays within {TOL} of the reference ({_fmt(new)})."
            log(f"withhold {t}")
        else:
            c["tables"][t]["action"] = "release"
            c["tables"][t]["reason"] = f"Released: without it {_fmt({k: v for k, v in new.items() if v < ref[k] - TOL})}."
        trail.append({"table": t, "column": "(table)", "decision": c["tables"][t]["action"], "scores": new})

    cols = [(t, col) for t in orig if c["tables"][t]["action"] == "release" for col in orig[t].columns]
    cols.sort(key=lambda tc: RISK_ORDER.get(info[tc]["role"], 9))
    released = [t for t in orig if c["tables"][t]["action"] == "release"]
    qi_count = {t: sum(info[(t, col)]["role"] == "quasi_identifier" for col in orig[t].columns) for t in released}
    main_ref = max(qi_count, key=qi_count.get) if qi_count and max(qi_count.values()) else None
    roles_of = {t: dict(labels[labels.table == t][["column", "privacy_role"]].itertuples(index=False)) for t in orig}

    def risk_of(t, judged=None):
        """Risk of table t as the contract stands, before the k repair; with judged given, every column of t outside
        it counts as dropped. Keyed columns never enter the count, so they are dropped here to skip the HMAC."""
        spec = {col: (r if (judged is None or (t, col) in judged) and r["pet"] not in KEYED else {**DROP, "reason": "r"})
                for col, r in c["columns"][t].items()}
        cc = {**c, "columns": {**c["columns"], t: spec}}
        frame, _, _ = protect.protect_table(t, orig[t], cc, key, roles_of[t])
        return risk(frame, t, cc, labels)

    def distinct_of(t, col):
        """Distinct values of col after its current PET on its own table: drop 0, a keyed token as many as the source
        (the HMAC is one to one), otherwise counted on the protected column."""
        rule = c["columns"][t][col]
        if rule["pet"] == "drop":
            return 0
        if rule["pet"] in KEYED:
            return int(orig[t][col].nunique())
        sub = list(dict.fromkeys([col, c["tables"][t]["record_id"], *([rule["params"]["since"]] if rule["pet"] == "duration" else [])]))
        spec = {**{x: {**DROP, "reason": "r"} for x in sub}, col: rule}
        frame, _, _ = protect.protect_table(t, orig[t][sub], {**c, "columns": {**c["columns"], t: spec}}, key, roles_of[t])
        return int(frame[_released_name(col, rule)].nunique())

    judged = set()
    for t, col in cols:
        w = info[(t, col)]
        for rule, name in w["ladder"]:
            c["columns"][t][col] = {**rule, "reason": "pending"}
            new = score_now() if len(w["ladder"]) > 1 or rule["pet"] != "drop" else ref
            r, used = risk_of(t, judged | {(t, col)})
            w["tried"].append({"candidate": name, "scores": new, "ok": ok(new), "risk": r, "distinct": distinct_of(t, col), "knowable": used})
        pick, w["why"] = _decide(w["tried"])
        rule = next(rr for rr, n in w["ladder"] if n == pick["candidate"])
        c["columns"][t][col] = {**rule, "reason": "pending"}
        w["chosen"], w["pick"] = pick["candidate"], pick
        judged.add((t, col))
        trail.append({"table": t, "column": col, "role": w["role"], "subtype": w["subtype"], "chosen": w["chosen"],
                      "rule": w["why"], "risk_line": RISK_LINE, "tried": w["tried"]})
        log(f"{t}.{col} ({w['role']}, {w['subtype']}): {w['chosen']} (risk {pick['risk']:.4f}, {w['why']})")

    for (t, col), w in info.items():
        if c["tables"][t]["action"] == "withhold":
            continue
        rule = c["columns"][t][col]
        head = f"Detected {w['role']} ({w['subtype'] or 'no subtype'})."
        if len(w["ladder"]) == 1:
            x = w["tried"][0]
            rule["reason"] = (f"{head} The only candidate for this type is drop (utility {_fmt(x['scores'])}; risk {x['risk']:.4f};"
                              f" risk line {RISK_LINE}).")
            continue
        rule["reason"] = f"{head} Candidates tried: {_tried_text(w['tried'])}. {_chosen_text(w['chosen'], w['pick'], w['why'], tried=w['tried'])}"
        if rule["pet"] == "token":
            rule["reason"] += " A keyed HMAC-SHA256 token keeps joins and carries no order, which a sequential id would give back."
    for t in [t for t in c["tables"] if c["tables"][t]["action"] == "withhold"]:
        c["columns"].pop(t, None)
        c["roles"].pop(t, None)

    def repaired_release():
        kt = _k_target(c, info, main_ref)
        prot = _release(c, orig, key, labels)
        if kt:
            main = kt["table"]
            keys = lambda t, col: set(orig[t][col].dropna())  # noqa: E731
            prot[main], _, _ = protect.repair_released(prot[main], orig[main], kt, list(kt["ladder"]), keys)
        return prot

    def repaired_now():
        return _scores(utility_fn(domain, orig, repaired_release(), scen), required)

    after = repaired_now()
    log(f"after the k repair: {_fmt(after)}")
    moves = []
    for _ in range(3):
        moved = False
        for t, col in [tc for tc in cols if info[tc]["role"] == "quasi_identifier"]:
            w = info[(t, col)]
            prev = c["columns"][t][col]
            tried = []
            for rule, name in w["ladder"]:
                c["columns"][t][col] = {**rule, "reason": "pending"}
                new = after if name == w["chosen"] else repaired_now()
                r, used = risk_of(t)
                tried.append({"candidate": name, "scores": new, "ok": _mean(new) >= _mean(after) - 1e-9, "risk": r,
                              "distinct": distinct_of(t, col), "knowable": used})
            pick, why = _decide(tried)
            w["repair"] = {"tried": tried, "why": why, "pick": pick}
            if pick["candidate"] == w["chosen"]:
                c["columns"][t][col] = prev
                continue
            rule = next(rr for rr, n in w["ladder"] if n == pick["candidate"])
            c["columns"][t][col] = {**rule, "reason": "pending"}
            moves.append({"table": t, "column": col, "from": w["chosen"], "to": pick["candidate"], "rule": why,
                          "scores_before": after, "scores_after": pick["scores"], "tried": tried})
            log(f"after the k repair, {t}.{col}: {w['chosen']} -> {pick['candidate']} ({_fmt(pick['scores'])}, risk {pick['risk']:.4f})")
            w["k_aware"] = {"from": w["chosen"], "before": after, "after": pick["scores"], "tried": tried, "why": why, "pick": pick}
            w["chosen"], after, moved = pick["candidate"], pick["scores"], True
        if not moved:
            break
    for (t, col), w in info.items():
        if w.get("k_aware") and c["tables"][t]["action"] == "release":
            k = w["k_aware"]
            c["columns"][t][col]["reason"] = (
                f"Detected {w['role']} ({w['subtype'] or 'no subtype'}). Candidates tried before the k repair: {_tried_text(w['tried'])}."
                f" Scored again on the repaired release (feasible: mean utility no worse than {k['from']}, {_fmt(k['before'])}):"
                f" {_tried_text(k['tried'], 'no worse', 'worse', 'than the current choice')}."
                f" {_chosen_text(w['chosen'], k['pick'], k['why'], repaired=True, tried=k['tried'])}")

    final = score_now()
    log(f"final: {_fmt(final)}")
    kt = _k_target(c, info, main_ref)
    if kt:
        c["k_target"] = kt
        c["k_columns"] = kt["columns"]

    prot = repaired_release()
    post, fit = {}, {}
    for t, frame in prot.items():
        share, used = risk(frame, t, c, labels)
        post[t] = {"risk": round(share, 4), "knowable": used, "line_met": share < RISK_LINE}
        log(f"{t}: knowable columns {', '.join(used) or 'none'}; risk after the k repair {share:.4f}")
        for col, rule in c["columns"][t].items():
            if _released_name(col, rule) in used:
                rule["reason"] += (f" {'After the k repair' if kt else 'On the final release'}, risk on the knowable columns of {t} ({', '.join(used)}) is {share:.4f}: "
                                   + ("line met." if share < RISK_LINE else "line not met after repair."))
        fshare, fcols = _fitness(frame, t, c, labels)
        fit[t] = {"n_rows": int(len(frame)), "columns": fcols, "share_k_below_5": round(fshare, 4)}
    c["fitness"] = {"trust_level": scen["trust_level"], "k": K, "tables": fit,
                    "rule": ("Share of the released rows whose combination of every kept value (every kept column except keyed"
                             " tokens and free text) is shared by fewer than 5 rows, on the final release after the k repair."
                             " Reported for the fit-for-sharing statement; it decides nothing in selection.")}
    evidence = {"scenario": scenario_id, "required_tasks": required, "tolerance": TOL, "risk_line": RISK_LINE, "min_gain": MIN_GAIN, "k": K,
                "knowable_rule": KNOWABLE_RULE,
                "main_table": main_ref, "reference_scores": ref, "final_scores_before_repair": final,
                "final_scores_after_repair": after, "risk_after_repair": post, "fitness": c["fitness"],
                "moved_after_repair": moves, "trail": trail}
    return c, evidence


def _ladder_step(col, rule, subtype=""):
    pet, prm = rule["pet"], rule.get("params", {})
    if pet == "age_band" and prm.get("width", 10) < 20:
        return {"column": col, "op": "widen_band", "width": 20, "reason": "At-risk rows only: age band widened to 20 years."}
    if pet == "top_n_exact_else_other" or (pet == "keep" and subtype in PLACE):
        return {"column": col, "op": "set", "value": "other", "reason": "At-risk rows only: place becomes other."}
    if pet == "hour_of_day":
        return {"column": col, "op": "widen_hour", "block": 3, "reason": "At-risk rows only: hour widened to a 3-hour block."}
    if pet == "round_decimals" and prm.get("decimals", 2) > 1:
        return {"column": col, "op": "round", "decimals": prm["decimals"] - 1, "reason": "At-risk rows only: coordinate grid made 10 times coarser."}
    if pet == "day":
        return {"column": col, "op": "to_month", "reason": "At-risk rows only: date coarsened to its month."}
    if pet == "date_hour":
        return {"column": col, "op": "to_day", "reason": "At-risk rows only: hour dropped, date kept."}
    if pet == "prefix" and prm.get("n", 2) > 1:
        return {"column": col, "op": "prefix", "n": prm["n"] - 1, "reason": "At-risk rows only: one postcode digit fewer."}
    return None


def _k_target(c, info, main=None):
    """main: the table fixed from the reference release; when it keeps no quasi-identifier, the table keeping most."""
    kept = {t: [col for col, r in cols.items() if r["pet"] != "drop" and info[(t, col)]["role"] == "quasi_identifier"]
            for t, cols in c["columns"].items()}
    if not any(kept.values()):
        return None
    if not kept.get(main):
        main = max(kept, key=lambda t: len(kept[t]))
    cols = kept[main]
    live = {col: r for col, r in c["columns"][main].items() if r["pet"] != "drop"}
    diag = [col for col in live if info[(main, col)]["subtype"] == "DIAGNOSIS_CODE"]
    sens = [col for col in live if info[(main, col)]["role"] == "sensitive_attribute"]
    linked = {col: live[col].get("params", {}).get("also_as") for col in cols if live[col].get("params", {}).get("also_as")}
    ladder = {}
    for col in cols:
        step = _ladder_step(col, live[col], info[(main, col)]["subtype"])
        if step:
            ladder[f"{col}:{step['op']}"] = step
    s = (diag or sens or [None])[0]
    # another released table joined on the main table's record key shows which rows have rows there: an attacker
    # holding the release knows it, so it joins the group key of the repair
    rid = c["tables"][main]["record_id"]
    flags = [{"table": t, "on": rid} for t, tc in c["columns"].items()
             if t != main and rid in tc and tc[rid]["pet"] != "drop" and live.get(rid, DROP)["pet"] != "drop"]
    return {"table": main, **({"join_flags": flags} if flags else {}), "k": 5, "l": 2 if s else 1, **({"sensitive": s} if s else {}),
            "columns": cols, "linked": linked, "ladder": ladder,
            "reason": f"Every released {main} row shares its kept quasi-identifiers ({', '.join(cols)}) with at least 4 other rows"
                      + (f", and every such group holds at least 2 distinct {s} values" if s else "")
                      + "; only the rows that miss the target are coarsened, and rows still at risk get those columns suppressed."}
