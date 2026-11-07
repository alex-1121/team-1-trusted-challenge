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


def test_selector_takes_the_most_private_candidate_that_keeps_the_task(tmp_path):
    from pets_transformer import selector
    d = tmp_path / "toy"
    d.mkdir()
    ts = [f"2025-0{1 + i % 9}-1{i % 9} {i % 24:02d}:15:00" for i in range(40)]
    pd.DataFrame({"rec": [f"RC-{i:05d}" for i in range(40)], "ts": ts}).to_csv(d / "t.csv", index=False)
    labels = pd.DataFrame({"dataset": "toy", "table": "t", "column": ["rec", "ts"],
                           "privacy_role": ["record_key", "quasi_identifier"], "subtype": ["RECORD_ID", "TIMESTAMP"]})
    scen = {"id": "TOY", "recipient": "r", "purpose": "p", "trust_level": "t", "threat_model": "m", "utility_requirements": ["U1"]}

    def util(domain, orig, prot, scen):  # U1 needs the month of ts
        t = prot.get("t", pd.DataFrame())
        good = "ts" in t and t.ts.astype(str).str[:7].eq(orig["t"].ts.str[:7]).all()
        return [{"id": "U1", "score": 1.0 if good else 0.0}]
    c, _ = selector.select(d, "TOY", tmp_path, labels=labels, scen=scen, utility_fn=util, log=lambda *_: None)
    assert c["columns"]["t"]["ts"]["pet"] == "month"
