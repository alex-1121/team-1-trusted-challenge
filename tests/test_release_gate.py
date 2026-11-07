import json
from pathlib import Path

import pandas as pd

from pets_transformer import contract as ct
from pets_transformer import pets, protect, redteam, repair

C = ct.load(Path(__file__).parent.parent / "contracts" / "HEALTH-S1.json")
KEY = b"k" * 32


def test_token_same_value_same_token_across_tables_and_keyed():
    a = pets.token(pd.Series(["ED25-000001", "ED25-000002"]), KEY, "V")
    b = pets.token(pd.Series(["ED25-000002"]), KEY, "V")
    c = pets.token(pd.Series(["ED25-000002"]), b"z" * 32, "V")
    assert a[1] == b[0] != c[0] and a[0] != a[1]
    # a token differs from the pseudonym of the same value under the same key (domain separation)
    assert pets.token(pd.Series(["x"]), KEY, "P")[0] != pets.hmac_pseudonym(pd.Series(["x"]), KEY)[0]


def test_shuffle_moves_rows_and_row_map_follows():
    df = pd.DataFrame({"id": [f"r{i}" for i in range(50)], "v": [str(i) for i in range(50)]})
    rm = pd.DataFrame({"protected_row": range(50), "original_record_id": df.id})
    out, rm2 = protect.shuffle(df, rm, seed=1)
    assert list(out.id) != list(df.id)
    assert list(rm2.original_record_id) == list(out.id) and list(rm2.protected_row) == list(range(50))


TARGET = {"table": "t", "k": 3, "l": 1, "columns": ["age", "town"], "linked": {"age": ["age_copy"]},
          "ladder": {"age20": {"column": "age", "op": "widen_band", "width": 20, "reason": "r"},
                     "town": {"column": "town", "op": "set", "value": "other", "reason": "r"}}, "reason": "r"}


def test_repair_reaches_k_and_only_touches_rows_at_risk():
    df = pd.DataFrame({"age": ["30-39"] * 5 + ["40-49", "50-59", "20-29"], "town": ["A"] * 5 + ["B", "C", "D"]})
    df["age_copy"] = df.age
    out, keep, rep = repair.apply(df, TARGET, ["age20", "town"])
    assert rep["at_risk_after"] == 0 and rep["share_at_risk_before"] == 0.375
    assert (out.age[:5] == "30-39").all()  # the safe group is untouched
    assert out.age.equals(out.age_copy)
    assert out.groupby(["age", "town"]).size().min() >= 3


def test_repair_l_diversity_merges_single_diagnosis_group():
    t = {**TARGET, "k": 2, "l": 2, "sensitive": "dx"}
    df = pd.DataFrame({"age": ["30-39"] * 3 + ["40-49"] * 3, "town": ["A"] * 6, "dx": ["J10"] * 3 + ["J10", "S06", "K80"]})
    df["age_copy"] = df.age
    out, keep, rep = repair.apply(df, t, ["age20", "town"])
    assert rep["at_risk_before"] == 3 and rep["at_risk_after"] == 0
    assert out.groupby(["age", "town"]).dx.nunique().min() >= 2


def test_widen_band_edges():
    assert repair._widen_band("30-39", 20) == "20-39" and repair._widen_band("80+", 20) == "80+"
    assert repair._widen_band("70-79", 20) == "60-79" and repair._widen_band("suppressed", 20) == "suppressed"


def _visits(n=240, sequential=True):
    hours = [f"{h:02d}:00" for d in range(n // 8) for h in (1, 4, 7, 10, 13, 16, 19, 22)]
    dates = [f"2025-01-{1 + d:02d}" for d in range(n // 8) for _ in range(8)]
    ids = [f"ED25-{i:06d}" for i in range(n)]
    orig = pd.DataFrame({"visit_id": ids, "arrival_ts": [f"{d} {h}:00" for d, h in zip(dates, hours)]})
    rel = pd.DataFrame({"visit_id": ids if sequential else list(pets.token(pd.Series(ids), KEY, "V")), "arrival_ts": hours})
    return orig, rel


def test_order_attack_rebuilds_dates_from_sequential_ids_and_not_from_shuffled_tokens():
    orig, rel = _visits()
    dates = orig.arrival_ts.str[:10]
    leak, _ = redteam.order_attack(rel, dates, "ed_visits", "arrival_ts", {})
    assert leak["share_rows_date_rebuilt"] == 1.0
    _, tok = _visits(sequential=False)
    rm = pd.DataFrame({"protected_row": range(len(tok)), "original_record_id": orig.visit_id})
    shuf, rm2 = protect.shuffle(tok, rm, seed=3)
    safe, _ = redteam.order_attack(shuf, orig.set_index("visit_id").arrival_ts.reindex(rm2.original_record_id).str[:10].reset_index(drop=True),
                                   "ed_visits", "arrival_ts", {})
    assert safe["share_rows_date_rebuilt"] < 0.2


def test_fingerprint_not_applicable_without_person_key():
    _, rel = _visits()
    assert redteam.person_fingerprint(rel, [], ["arrival_ts"], "arrival_ts")["applicable"] is False


def test_shipped_contract_has_k_target_and_no_sequential_keys_kept():
    assert C["k_target"]["k"] == 5 and C["k_target"]["l"] == 2
    for t in ("ed_visits", "lab_results"):
        assert C["roles"][t]["record_key"]["pet"] == "token"
    assert C["columns"]["ed_visits"]["visit_id"]["pet"] == C["columns"]["lab_results"]["visit_id"]["pet"] == "token"
    assert C["columns"]["ed_visits"]["visit_id"]["params"] == C["columns"]["lab_results"]["visit_id"]["params"]


def _tiny(tmp_path):
    d = tmp_path / "toy"
    d.mkdir()
    n = 40
    pd.DataFrame({"rec": [f"RC-{i:05d}" for i in range(n)], "secret": [f"secret{i}" for i in range(n)],
                  "colour": ["red", "blue"] * (n // 2), "size": [str(i % 7) for i in range(n)]}).to_csv(d / "t.csv", index=False)
    labels = pd.DataFrame({"dataset": "toy", "table": "t", "column": ["rec", "secret", "colour", "size"],
                           "privacy_role": ["record_key", "direct_identifier", "non_sensitive", "non_sensitive"],
                           "subtype": ["RECORD_ID", "OTHER", "CATEGORY", "MEASUREMENT"]})
    return d, labels


def test_selector_keeps_only_what_a_task_needs(tmp_path):
    from pets_transformer import selector
    d, labels = _tiny(tmp_path)
    scen = {"id": "TOY-S1", "recipient": "r", "purpose": "p", "trust_level": "t", "threat_model": "m", "utility_requirements": ["U1"]}

    def util(domain, orig, prot, scen):  # U1 needs the colour column only
        return [{"id": "U1", "score": 1.0 if "colour" in prot.get("t", pd.DataFrame()).columns else 0.0}]
    c, ev = selector.select(d, "TOY-S1", tmp_path, labels=labels, scen=scen, utility_fn=util, log=lambda *_: None)
    cols = c["columns"]["t"]
    assert cols["colour"]["pet"] == "keep" and "drop: outside" in cols["colour"]["reason"]
    assert cols["size"]["pet"] == "drop" and cols["secret"]["pet"] == "drop" and cols["rec"]["pet"] == "drop"
    assert ct_load_ok(c)


def ct_load_ok(c):
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(c, f)
    return ct.load(f.name) is not None


def test_plain_hash_is_caught_and_keyed_token_is_not(tmp_path):
    import hashlib
    o, p = tmp_path / "o", tmp_path / "p"
    o.mkdir(), p.mkdir()
    ids = [f"010190-{i:03d}A" for i in range(30)]
    pd.DataFrame({"id": ids}).to_csv(o / "t.csv", index=False)
    pd.DataFrame({"plain": [hashlib.sha256(x.encode()).hexdigest() for x in ids],
                  "keyed": list(pets.token(pd.Series(ids), KEY, "T").str[1:].str.ljust(64, "0"))}).to_csv(p / "t.csv", index=False)
    r = redteam.plain_hash(p, o)
    shares = {x["column"]: x["share_reversed"] for x in r["hash_like_columns"]}
    assert shares["plain"] == 1.0 and shares["keyed"] == 0.0 and r["worst_share_reversed"] == 1.0


def test_contract_without_hour_column_has_no_order_attack():
    assert redteam._time_column({"columns": {"t": {"a": {"pet": "keep"}}}}) == (None, None)


def _ts_toy(tmp_path, ts):
    d = tmp_path / "toy"
    d.mkdir()
    pd.DataFrame({"rec": [f"RC-{i:05d}" for i in range(len(ts))], "ts": ts}).to_csv(d / "t.csv", index=False)
    labels = pd.DataFrame({"dataset": "toy", "table": "t", "column": ["rec", "ts"],
                           "privacy_role": ["record_key", "quasi_identifier"], "subtype": ["RECORD_ID", "TIMESTAMP"]})
    scen = {"id": "TOY", "recipient": "r", "purpose": "p", "trust_level": "t", "threat_model": "m", "utility_requirements": ["U1"]}
    return d, labels, scen


def test_selector_takes_the_most_useful_candidate_under_the_risk_line(tmp_path):
    from pets_transformer import selector
    # 80 rows on 8 dates, 10 per date, hours spread: date is under the line, date and hour is not
    ts = [f"2025-01-0{1 + i // 10} {i % 24:02d}:15:00" for i in range(80)]
    d, labels, scen = _ts_toy(tmp_path, ts)

    def util(domain, orig, prot, scen):  # U1: 0.96 for the right month, 1.0 when the date is right too
        t = prot.get("t", pd.DataFrame())
        if "ts" not in t:
            return [{"id": "U1", "score": 0.0}]
        p, o = t.ts.astype(str), orig["t"].ts
        return [{"id": "U1", "score": 0.96 * p.str[:7].eq(o.str[:7]).mean() + 0.04 * p.str[:10].eq(o.str[:10]).mean()}]
    c, ev = selector.select(d, "TOY", tmp_path, labels=labels, scen=scen, utility_fn=util, log=lambda *_: None)
    rule = c["columns"]["t"]["ts"]
    # month is coarser and also under the line; the rule takes utility, not the most private candidate
    assert rule["pet"] == "day"
    tried = {x["candidate"]: x for x in next(x for x in ev["trail"] if x["column"] == "ts")["tried"]}
    assert tried["month"]["ok"] and tried["month"]["risk"] < selector.RISK_LINE
    assert tried["date and hour"]["ok"] and tried["date and hour"]["risk"] >= selector.RISK_LINE
    assert f"risk line {selector.RISK_LINE}" in rule["reason"] and "risk 0.0000" in rule["reason"] and "utility U1" in rule["reason"]
    assert c["fitness"]["trust_level"] == "t" and c["fitness"]["tables"]["t"]["n_rows"] == 80


def test_selector_takes_the_candidate_under_the_risk_line_when_utility_ties(tmp_path):
    from pets_transformer import selector
    ts = [f"2025-0{1 + i % 4}-1{i % 9} {i % 24:02d}:15:00" for i in range(40)]  # 10 rows per month, dates mostly unique
    d, labels, scen = _ts_toy(tmp_path, ts)

    def util(domain, orig, prot, scen):  # U1 needs the month of ts: month, date and date and hour all score 1.0
        t = prot.get("t", pd.DataFrame())
        good = "ts" in t and t.ts.astype(str).str[:7].eq(orig["t"].ts.str[:7]).all()
        return [{"id": "U1", "score": 1.0 if good else 0.0}]
    c, ev = selector.select(d, "TOY", tmp_path, labels=labels, scen=scen, utility_fn=util, log=lambda *_: None)
    tried = {x["candidate"]: x for x in next(x for x in ev["trail"] if x["column"] == "ts")["tried"]}
    assert tried["date"]["scores"] == tried["month"]["scores"] and tried["date"]["ok"]
    assert tried["date"]["risk"] >= selector.RISK_LINE > tried["month"]["risk"]
    # "date" sorts before "month", so only the risk can have decided
    assert c["columns"]["t"]["ts"]["pet"] == "month"


def test_risk_leaves_measurements_and_sensitive_values_out_of_the_knowable_set():
    from pets_transformer import selector
    n = 30
    frame = pd.DataFrame({"rate": [str(10 + i) for i in range(n)], "town": ["A", "B", "C"] * 10,
                          "temp": [f"36.{i}" for i in range(n)], "dx": [f"J{i:02d}" for i in range(n)],
                          "code": [f"C{i % 25}" for i in range(n)]})
    labels = pd.DataFrame({"dataset": "x", "table": "t", "column": list(frame.columns),
                           "privacy_role": ["quasi_identifier", "quasi_identifier", "non_sensitive", "sensitive_attribute", "non_sensitive"],
                           "subtype": ["AGE", "MUNICIPALITY", "MEASUREMENT", "DIAGNOSIS_CODE", "CATEGORY"]})
    contract = {"columns": {"t": {col: {"pet": "keep"} for col in frame.columns}}}
    share, cols = selector.risk(frame, "t", contract, labels)
    # a numeric quasi-identifier stays in; a measurement, a sensitive value and a 25-value category stay out
    assert cols == ["rate", "town"] and share == 1.0
    contract["columns"]["t"]["rate"] = {"pet": "drop"}
    assert selector.risk(frame, "t", contract, labels) == (0.0, ["town"])


def test_selector_drops_a_column_no_task_needs_when_utility_and_risk_tie(tmp_path):
    from pets_transformer import selector
    d = tmp_path / "toy"
    d.mkdir()
    pd.DataFrame({"rec": [f"RC-{i:05d}" for i in range(40)], "town": ["A", "B", "C", "D"] * 10}).to_csv(d / "t.csv", index=False)
    labels = pd.DataFrame({"dataset": "toy", "table": "t", "column": ["rec", "town"],
                           "privacy_role": ["record_key", "quasi_identifier"], "subtype": ["RECORD_ID", "MUNICIPALITY"]})
    scen = {"id": "TOY", "recipient": "r", "purpose": "p", "trust_level": "t", "threat_model": "m", "utility_requirements": ["U1"]}
    def util(domain, orig, prot, scen):  # U1 needs the table released, no column of it
        return [{"id": "U1", "score": 1.0 if "t" in prot else 0.0}]
    c, ev = selector.select(d, "TOY", tmp_path, labels=labels, scen=scen, utility_fn=util, log=lambda *_: None)
    tried = next(x for x in ev["trail"] if x["column"] == "town")["tried"]
    # every candidate scores 1.0 with risk 0; "8 most common, rest other" sorts before "drop", so the name alone would keep it
    assert {x["risk"] for x in tried} == {0.0} and len({x["scores"]["U1"] for x in tried}) == 1
    rule = c["columns"]["t"]["town"]
    assert rule["pet"] == "drop" and "ties: lower risk, then fewer distinct values, then name" in rule["reason"]


def _gain_toy(tmp_path, gain):
    from pets_transformer import selector
    d = tmp_path / "toy"
    d.mkdir()
    pd.DataFrame({"rec": [f"RC-{i:05d}" for i in range(40)], "colour": ["A", "B", "C", "D"] * 10}).to_csv(d / "t.csv", index=False)
    labels = pd.DataFrame({"dataset": "toy", "table": "t", "column": ["rec", "colour"],
                           "privacy_role": ["record_key", "non_sensitive"], "subtype": ["RECORD_ID", "CATEGORY"]})
    scen = {"id": "TOY", "recipient": "r", "purpose": "p", "trust_level": "t", "threat_model": "m", "utility_requirements": ["U1", "U2"]}

    def util(domain, orig, prot, scen):  # U1 gains `gain` with colour kept; U2 does not need it
        t = prot.get("t", pd.DataFrame())
        return [{"id": "U1", "score": 0.9 + (gain if "colour" in t.columns else 0.0)}, {"id": "U2", "score": 1.0 if "t" in prot else 0.0}]
    c, ev = selector.select(d, "TOY", tmp_path, labels=labels, scen=scen, utility_fn=util, log=lambda *_: None)
    tried = {x["candidate"]: x for x in next(x for x in ev["trail"] if x["column"] == "colour")["tried"]}
    return c["columns"]["t"]["colour"], tried


def test_selector_drops_a_column_that_gains_less_than_min_gain_over_drop(tmp_path):
    from pets_transformer import selector
    rule, tried = _gain_toy(tmp_path, 0.005)
    assert abs(tried["kept"]["gain_over_drop"] - 0.005) < 1e-9 and tried["kept"]["ok"] and tried["kept"]["risk"] < selector.RISK_LINE
    assert rule["pet"] == "drop"
    assert f"no candidate improves a required task by at least {selector.MIN_GAIN} over drop" in rule["reason"]


def test_selector_keeps_a_column_that_gains_more_than_min_gain_over_drop(tmp_path):
    from pets_transformer import selector
    rule, tried = _gain_toy(tmp_path, 0.02)
    assert abs(tried["kept"]["gain_over_drop"] - 0.02) < 1e-9
    assert rule["pet"] == "keep" and f"by at least {selector.MIN_GAIN} over drop" in rule["reason"]


def test_min_gain_does_not_apply_when_drop_breaks_a_required_task():
    from pets_transformer import selector
    # ok is set by hand: with one task and TOL 0.05 the main pass cannot make this pair, the repair pass (mean
    # no worse than the current choice) can
    tried = [{"candidate": "drop", "scores": {"U1": 0.94}, "ok": False, "risk": 0.0, "distinct": 0},
             {"candidate": "month", "scores": {"U1": 0.945}, "ok": True, "risk": 0.0, "distinct": 12}]
    pick, why = selector._decide(tried)
    assert pick["candidate"] == "month" and why == "line" and abs(pick["gain_over_drop"] - 0.005) < 1e-9
    assert "drop breaks a required task, so the gain rule does not apply" in selector._chosen_text("month", pick, why, tried=tried).lower()


def test_selector_never_reads_the_menu_order(tmp_path, monkeypatch):
    from pets_transformer import selector
    d, labels = _tiny(tmp_path)
    scen = {"id": "TOY-S1", "recipient": "r", "purpose": "p", "trust_level": "t", "threat_model": "m", "utility_requirements": ["U1"]}

    def util(domain, orig, prot, scen):
        return [{"id": "U1", "score": 1.0 if "colour" in prot.get("t", pd.DataFrame()).columns else 0.0}]

    def pets_of(c):
        return {col: (r["pet"], r.get("params")) for col, r in c["columns"]["t"].items()}
    first, _ = selector.select(d, "TOY-S1", tmp_path, labels=labels, scen=scen, utility_fn=util, log=lambda *_: None)
    menu = selector.candidates
    monkeypatch.setattr(selector, "candidates", lambda role, sub: list(reversed(menu(role, sub))))
    second, _ = selector.select(d, "TOY-S1", tmp_path, labels=labels, scen=scen, utility_fn=util, log=lambda *_: None)
    assert pets_of(first) == pets_of(second)
    # size and rec tie on utility and risk under both orders; distinct values decide before the name (drop counts as 0)
    assert pets_of(second)["size"][0] == "drop" and pets_of(second)["rec"][0] == "drop"


def test_hour_block_is_explicit_and_covers_its_hours():
    from pets_transformer import generalise as g
    from pets_transformer import repair as rp
    assert rp._widen_hour("07:00", 3) == "06:00 to 08:59"
    assert rp._widen_hour("06:00 to 08:59", 3) == "06:00 to 08:59"
    assert g.hours("06:00 to 08:59") == {6, 7, 8} and g.hours("suppressed") == set(range(24))
    step = {"op": "widen_hour", "block": 3}
    assert g.covers("06:00 to 08:59", "07:00", [step]) and not g.covers("06:00 to 08:59", "09:00", [step])
    assert g.covers("20-39", "30-39", [{"op": "widen_band", "width": 20}]) and not g.covers("20-39", "40-49", [{"op": "widen_band"}])
    assert g.covers("other", "Turku", [{"op": "set", "value": "other"}]) and not g.covers("other", "Turku")
    assert g.covers("suppressed", "anything")


def test_informed_attacker_counts_generalised_rows_as_matches():
    import pandas as pd
    from pets_transformer import checks as ck
    # Released: one exact row "a/07:00" and one block row covering 06-08. The attacker for R1 sees two candidates.
    att = pd.DataFrame({"m": ["a", "a", "b"], "h": ["07:00", "08:00", "07:00"], "record_id": ["R1", "R2", "R3"]})
    rel = pd.DataFrame({"m": ["a", "a", "b"], "h": ["07:00", "06:00 to 08:59", "07:00"]})
    ops = {"h": [{"op": "widen_hour", "block": 3}]}
    r = ck.singled_out_covering(att, rel, ["R1", "R2", "R3"], ["m", "h"], ops)
    # R1 matches both a-rows; R2 matches only the block row (correct); R3 matches its own row (correct)
    assert r["n_singled_out"] == 2 and r["n_correct"] == 2


def test_date_hour_pet_and_to_day_repair():
    import pandas as pd
    from pets_transformer import pets, repair, selector
    assert pets.date_hour(pd.Series(["2025-12-01T07:42", None])).tolist()[0] == "2025-12-01T07:00"
    assert repair._op(pd.Series(["2025-12-01T07:00", "2025-12"]), {"op": "to_day"}).tolist() == ["2025-12-01", "2025-12"]
    names = [n for _, n in selector.candidates("quasi_identifier", "TIMESTAMP")]
    assert names[-1] == "date and hour" and names.index("hour of day") < names.index("date and hour")


def test_selector_moves_a_column_when_the_repair_would_wipe_it_out(tmp_path):
    from pets_transformer import selector
    d = tmp_path / "toy"
    d.mkdir()
    # 40 rows, every date distinct: "date" passes before the repair, but k>=5 can only hold on months (10 per month)
    ts = [f"2025-0{1 + i % 4}-{1 + i // 4:02d} 08:15:00" for i in range(40)]
    pd.DataFrame({"rec": [f"RC-{i:05d}" for i in range(40)], "ts": ts}).to_csv(d / "t.csv", index=False)
    labels = pd.DataFrame({"dataset": "toy", "table": "t", "column": ["rec", "ts"],
                           "privacy_role": ["record_key", "quasi_identifier"], "subtype": ["RECORD_ID", "TIMESTAMP"]})
    scen = {"id": "TOY", "recipient": "r", "purpose": "p", "trust_level": "t", "threat_model": "m", "utility_requirements": ["U1"]}

    def util(domain, orig, prot, scen):  # U1: half for the right month, half for the right date, per row
        t = prot.get("t", pd.DataFrame())
        if "ts" not in t or len(t) != 40:
            return [{"id": "U1", "score": 0.0}]
        p, o = t.ts.astype(str).values, orig["t"].ts.values
        return [{"id": "U1", "score": float(sum(0.5 * (a[:7] == b[:7]) + 0.5 * (a[:10] == b[:10]) for a, b in zip(p, o)) / 40)}]
    c, ev = selector.select(d, "TOY", tmp_path, labels=labels, scen=scen, utility_fn=util, log=lambda *_: None)
    # before the repair only the date keeps the task; after it, the date becomes the month anyway, so month is chosen
    ts_trail = next(x for x in ev["trail"] if x["column"] == "ts")
    assert ts_trail["chosen"] == "date"
    assert ev["moved_after_repair"] and ev["moved_after_repair"][0]["to"] == "month"
    assert c["columns"]["t"]["ts"]["pet"] == "month" and "repaired release" in c["columns"]["t"]["ts"]["reason"]


def test_duration_pet_replaces_two_timestamps_with_the_interval():
    import pandas as pd
    from pets_transformer import protect
    df = pd.DataFrame({"rid": ["R1", "R2"], "opened": ["2025-03-01T08:00", "2025-03-02T10:30"],
                       "closed": ["2025-03-01T20:00", "2025-03-05T10:30"]})
    c = {"tables": {"t": {"action": "release", "record_id": "rid"}},
         "columns": {"t": {"rid": {"pet": "drop", "reason": "r"}, "opened": {"pet": "month", "reason": "r"},
                           "closed": {"pet": "duration", "params": {"since": "opened", "as": "resolution_hours"}, "reason": "r"}}}}
    out, _, _ = protect.protect_table("t", df, c, b"k" * 32)
    assert list(out.columns) == ["opened", "resolution_hours"]
    assert out.resolution_hours.tolist() == ["12", "72"] and out.opened.tolist() == ["2025-03", "2025-03"]
