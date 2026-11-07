import pandas as pd
import pytest

from pets_transformer import contract as ct
from pets_transformer import protect as pr

C = ct.load(__import__("pathlib").Path(__file__).parent.parent / "contracts" / "HEALTH-S1.json")
LABELS = pd.read_csv(__import__("pathlib").Path(__file__).parent.parent / "results" / "detect" / "health_labels.csv", dtype=str)
ROLES = dict(LABELS[LABELS.table == "ed_visits"][["column", "privacy_role"]].itertuples(index=False))
COLS = list(ROLES)


def frame(n=30):
    rows = []
    for i in range(n):
        r = {c: "x" for c in COLS}
        r.update(visit_id=f"V{i}", patient_hetu=f"010190-{i % 3:03d}A", patient_name=f"Name{i % 3}",
                 date_of_birth=f"19{30 + i}-05-01", municipality=f"M{i % 10}", arrival_ts=f"2025-03-01 {i % 24:02d}:{i % 60:02d}:00")
        rows.append(r)
    return pd.DataFrame(rows)


def run(key=b"k" * 32, df=None):
    return pr.protect_table("ed_visits", frame() if df is None else df, C, key, ROLES)


def test_pseudonym_stable_and_keyed():
    a, _, _ = run()
    b, _, _ = run()
    c, _, _ = run(key=b"z" * 32)
    assert a.patient_hetu[0] == a.patient_hetu[3] != a.patient_hetu[1]
    assert a.patient_hetu.equals(b.patient_hetu) and not a.patient_hetu.equals(c.patient_hetu)
    assert a.patient_hetu.str.fullmatch(r"P[0-9a-f]{16}").all()


def test_no_original_identifier_survives():
    df = frame()
    out, _, _ = run(df=df)
    flat = set(out.astype(str).to_numpy().ravel())
    assert not flat & (set(df.patient_hetu) | set(df.patient_name))
    assert "patient_name" not in out.columns


def test_formats():
    out, _, _ = run()
    assert out.arrival_ts.str.fullmatch(r"\d\d:00").all()
    assert out.date_of_birth.str.fullmatch(r"\d0-\d9|80\+").all()
    assert out.age.equals(out.date_of_birth)


def test_plan_has_one_row_per_column():
    df = frame()
    _, _, plan = run(df=df)
    assert [r["column"] for r in plan] == list(df.columns)


def test_unnamed_column_raises():
    df = frame()
    df["surprise"] = "x"
    with pytest.raises(ValueError, match="surprise"):
        run(df=df)


def test_missing_hetu_stays_missing():
    df = frame()
    df.loc[[0, 1], "patient_hetu"] = None
    out, _, _ = run(df=df)
    assert out.patient_hetu[:2].isna().all() and out.patient_hetu[2:].notna().all()
