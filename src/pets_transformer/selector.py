"""Select: write the scenario contract from the detected labels and the scenario's required tasks.

Every column gets a ladder of candidate PETs for its detected role and subtype, from most private to least
(for a timestamp: drop, month, ISO week, hour of day, date, date and hour; for a birth date: drop, 20-year band, 10-year band; for a
place: drop, eight most common else "other", exact; for coordinates: drop, 2 decimals (about 1 km), 3 decimals
(about 100 m); for an identifier code: drop, keyed token; for a direct identifier or free text: drop only).

1. Reference: every column at its least private candidate, quasi-identifiers exact, direct identifiers dropped.
   The scenario's required tasks are scored on it with the organisers' utility code (run_utility). That is the
   most utility any candidate can keep.
2. Tables first: a table is withheld when no required task loses more than TOL without it.
3. Columns, riskiest first (quasi-identifiers, then identifier codes, sensitive values, plain values): each column
   takes the most private candidate that keeps every required task within TOL of the reference, with the choices
   already made in place. If no candidate does, the one with the best scores is taken and the reason says so.
4. k target for the main table (the one keeping most quasi-identifiers): the kept quasi-identifiers, l-diversity on
   a kept diagnosis code, join flags for tables joined on its key, and a repair ladder built from the chosen PETs.
5. After the repair: steps 3 and 4 judge a column before the k repair, and a quasi-identifier kept too fine makes
   the repair coarsen or suppress most rows. So every kept quasi-identifier is tried again one rung more private at a
   time, scored on the repaired release (k target rebuilt each time), and moved when the required tasks keep at
   least the same mean score. Rounds repeat until nothing moves (at most 3).

Every column rule states its reason with the measured scores. Neither the detector nor the ladders read column
names; names appear only as keys of the written contract.
"""
import json
from pathlib import Path

from pets_eval import io as pio
from pets_eval.scorecard import run_utility

from . import detect, protect
from . import repair as rp

TOL = 0.05
RISK_ORDER = {"quasi_identifier": 0, "technical_identifier": 1, "sensitive_attribute": 2, "free_text": 3,
              "non_sensitive": 4, "record_key": 5, "direct_identifier": 6}
PLACE = {"MUNICIPALITY", "LOCATION_NAME"}
TIME = {"TIMESTAMP", "DATE"}
DROP = {"pet": "drop"}
TOKEN = {"pet": "token", "params": {"prefix": "T"}}


def candidates(role, subtype):
    """(rule, short name) from most private to least. The reference release uses the last one, except that a
    quasi-identifier is exact in the reference (the most utility there is), so the ladder is measured against it."""
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
         "recipient": scen["recipient"], "purpose": scen["purpose"], "trust_level": scen["trust_level"],
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
            ref = {"pet": "keep"} if role == "quasi_identifier" else ladder[-1][0]
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
    for t, col in cols:
        w = info[(t, col)]
        chosen = None
        for rule, name in w["ladder"]:
            c["columns"][t][col] = {**rule, "reason": "pending"}
            new = score_now() if len(w["ladder"]) > 1 or rule["pet"] != "drop" else ref
            w["tried"].append({"candidate": name, "scores": new, "ok": ok(new)})
            if ok(new):
                chosen = (rule, name)
                break
        if chosen is None:
            best = max(w["tried"], key=lambda x: (min(x["scores"].values()), sum(x["scores"].values())))
            chosen = next((r, n) for r, n in w["ladder"] if n == best["candidate"])
            w["fallback"] = True
        c["columns"][t][col] = {**chosen[0], "reason": "pending"}
        w["chosen"] = chosen[1]
        trail.append({"table": t, "column": col, "role": w["role"], "subtype": w["subtype"], "chosen": chosen[1], "tried": w["tried"]})
        log(f"{t}.{col} ({w['role']}, {w['subtype']}): {chosen[1]}")

    for (t, col), w in info.items():
        if c["tables"][t]["action"] == "withhold":
            continue
        rule = c["columns"][t][col]
        head = f"Detected {w['role']} ({w['subtype'] or 'no subtype'})."
        if len(w["ladder"]) == 1:
            rule["reason"] = f"{head} The only candidate for this type is drop."
            continue
        tried = "; ".join(f"{x['candidate']}: {'within' if x['ok'] else 'outside'} {TOL} ({_fmt(x['scores'])})" for x in w["tried"])
        rule["reason"] = (f"{head} Candidates tried, most private first: {tried}. Chosen: {w['chosen']}"
                          + (" (no candidate stayed within the tolerance; best scores taken)." if w.get("fallback") else "."))
        if rule["pet"] == "token":
            rule["reason"] += " A keyed HMAC-SHA256 token keeps joins and carries no order, which a sequential id would give back."
    for t in [t for t in c["tables"] if c["tables"][t]["action"] == "withhold"]:
        c["columns"].pop(t, None)
        c["roles"].pop(t, None)

    def repaired_now():
        kt = _k_target(c, info)
        prot = _release(c, orig, key, labels)
        if kt:
            main = kt["table"]
            keys = lambda t, col: set(orig[t][col].dropna())  # noqa: E731
            prot[main], _, _ = protect.repair_released(prot[main], orig[main], kt, list(kt["ladder"]), keys)
        return _scores(utility_fn(domain, orig, prot, scen), required)

    def mean(sc):
        return sum(sc.values()) / max(len(sc), 1)

    after = repaired_now()
    log(f"after the k repair: {_fmt(after)}")
    moves = []
    for _ in range(3):
        moved = False
        for t, col in [tc for tc in cols if info[tc]["role"] == "quasi_identifier"]:
            w = info[(t, col)]
            names = [n for _, n in w["ladder"]]
            i = names.index(w["chosen"])
            for j in range(i - 1, -1, -1):
                rule, name = w["ladder"][j]
                prev = c["columns"][t][col]
                c["columns"][t][col] = {**rule, "reason": "pending"}
                new = repaired_now()
                if mean(new) >= mean(after) - 1e-9:
                    moves.append({"table": t, "column": col, "from": w["chosen"], "to": name, "scores_before": after, "scores_after": new})
                    log(f"after the k repair, {t}.{col}: {w['chosen']} -> {name} ({_fmt(new)})")
                    w["k_aware"] = {"from": w["chosen"], "before": after, "after": new}
                    w["chosen"], after, moved = name, new, True
                    break
                c["columns"][t][col] = prev
        if not moved:
            break
    for (t, col), w in info.items():
        if w.get("k_aware") and c["tables"][t]["action"] == "release":
            k = w["k_aware"]
            tried = "; ".join(f"{x['candidate']}: {'within' if x['ok'] else 'outside'} {TOL} ({_fmt(x['scores'])})" for x in w["tried"])
            c["columns"][t][col]["reason"] = (
                f"Detected {w['role']} ({w['subtype'] or 'no subtype'}). Candidates tried before the k repair, most private first: {tried}."
                f" Scored on the repaired release, {w['chosen']} keeps at least as much of the required tasks as {k['from']}"
                f" ({_fmt(k['after'])} against {_fmt(k['before'])}) and is more private, so it was chosen.")

    final = score_now()
    log(f"final: {_fmt(final)}")
    kt = _k_target(c, info)
    if kt:
        c["k_target"] = kt
        c["k_columns"] = kt["columns"]
    evidence = {"scenario": scenario_id, "required_tasks": required, "tolerance": TOL, "reference_scores": ref,
                "final_scores_before_repair": final, "final_scores_after_repair": after, "moved_after_repair": moves, "trail": trail}
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


def _k_target(c, info):
    kept = {t: [col for col, r in cols.items() if r["pet"] != "drop" and info[(t, col)]["role"] == "quasi_identifier"]
            for t, cols in c["columns"].items()}
    if not any(kept.values()):
        return None
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
