import pandas as pd

from pets_transformer import checks as ck


def test_l_diversity_shares_on_12_rows():
    # Four groups of three rows: diagnoses per group distinct 1, 2, 3, 3.
    df = pd.DataFrame({"date_of_birth": ["30-39"] * 12, "sex": ["F"] * 12,
                       "municipality": ["A"] * 3 + ["B"] * 3 + ["C"] * 3 + ["D"] * 3,
                       "arrival_ts": ["08:00"] * 12, "arrival_mode": ["walk-in"] * 12,
                       "icd10_primary": ["J18.9"] * 3 + ["J18.9", "J18.9", "I21.4"] + ["J18.9", "I21.4", "S72.0"] * 2})
    r = ck.l_diversity(df)
    assert r["n_groups"] == 4
    assert r["share_groups_l_below_2"] == 0.25 and r["share_groups_l_below_3"] == 0.5
    assert r["share_records_l_below_2"] == 0.25 and r["share_records_l_below_3"] == 0.5
    assert r["worst_group"]["size"] == 3 and r["worst_group"]["distinct"] == 1
    assert "J18.9" not in str(r)


def test_singled_out_with_known_row_map():
    released = pd.DataFrame({"a": ["x", "x", "y", "z", "w", "v"]})
    # Released rows are shuffled: the row map says which visit each row came from.
    records = ["V2", "V1", "V3", "V4", "V5", "V6"]
    attacker = pd.DataFrame({"a": ["x", "y", "z", "w", "q", "v"], "record_id": ["V1", "V3", "V9", "V5", "V6", "V6"]})
    r = ck.singled_out(attacker, released, records, ["a"])
    # x matches two rows; y, z, w, v match one; q matches none. z's row is V4, not the attacker's V9.
    assert r["n_singled_out"] == 4 and r["n_correct"] == 3
    assert r["singled_out_rate"] == round(4 / 6, 4) and r["correct_among_singled_out"] == 0.75


def test_joined_k_counts_visits_not_rows():
    ed = pd.DataFrame({"visit_id": [f"V{i}" for i in range(6)], "sex": ["F"] * 5 + ["M"], "icd10_primary": ["J18.9"] * 6})
    lab = pd.DataFrame({"visit_id": ["V0"] * 5 + ["V1", "V2", "V3", "V4", "V5"], "value": ["1"] * 10})
    r = ck.joined_k(ed, lab, ["sex", "icd10_primary", "value_not_there"])
    assert r["columns"] == ["sex", "icd10_primary"]
    assert r["n_joined_rows"] == 10 and r["n_visits"] == 6
    # F group: 5 visits over 9 rows (k 5); M group: 1 visit (k 1).
    assert r["share_rows_k_below_5"] == 0.1 and r["share_visits_k_below_5"] == round(1 / 6, 4)
    assert r["min_k"] == 1 and r["share_rows_k_below_5_counting_rows"] == 0.1


def test_catalogue_columns():
    cat = pd.DataFrame({"dataset": ["health"] * 4 + ["other"], "table": ["ed_visits", "ed_visits", "lab_results", "ed_visits", "ed_visits"],
                        "column": ["sex", "icd10_primary", "value", "triage", "x"],
                        "privacy_role": ["quasi_identifier", "sensitive_attribute", "sensitive_attribute", "sensitive_attribute", "quasi_identifier"],
                        "subtype": ["SEX", "DIAGNOSIS_CODE", "HEALTH_DATA", "HEALTH_DATA", "X"]})
    assert ck.catalogue_columns(cat, "health", ["ed_visits", "lab_results"]) == ["icd10_primary", "sex"]
