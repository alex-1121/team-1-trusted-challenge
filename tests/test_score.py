import pandas as pd

from pets_transformer import score as sc

CARD = {
    "summary": {"privacy": 0.9, "utility": 0.95, "composite": 0.92, "label": sc.LABEL},
    "utility": [{"id": "H-U2", "description": "LOS by triage", "score": 1.0}, {"id": "H-U6", "description": "Revisit", "score": 0.5}],
    "risk_components": {"ed_visits: records with k<5": 0.2, "ed_visits: linkage re-identification": 0.0},
    "tables": {"ed_visits": {"k_anonymity": {"qis": ["sex", "arrival_ts"], "median_k": 15.0, "min_k": 1, "share_below": {"k<5": 0.2}}}},
}
BASE = {"summary": {"privacy": 0.1, "utility": 1.0, "composite": 0.2}, "utility": [{"id": "H-U2", "score": 1.0}],
        "risk_components": {"ed_visits: records with k<5": 1.0, "ed_visits: linkage re-identification": 0.5}}


def test_summary_rows_and_residual():
    md = sc.build_summary(CARD, BASE, (0.3, 2), ["sex"], "S")
    assert "| H-U2 | LOS by triage | 1.0000 | 1.0000 |" in md
    assert "| H-U6 | Revisit | not run | 0.5000 |" in md
    assert "| ed_visits: records with k<5 | 1.0000 | 0.2000 |" in md
    assert "ed_visits, records with k<5, is 0.2: 20.0% of the records" in md
    assert "linkage re-identification, is" not in md
    assert "k<5 share 0.3000; min k 2" in md and sc.LABEL in md
    assert "—" not in md


def test_summary_without_baseline():
    assert "not run" in sc.build_summary(CARD, None, (0.0, 5), ["sex"], "S")


def test_rewrite_paths():
    t = '{"a": "/Users/bob/repo/data/x", "b": "/Users/bob/other/y"}'
    r = sc.rewrite_paths(t, ["/Users/bob/repo", "/Users/bob"])
    assert r == '{"a": "data/x", "b": "other/y"}'


def test_own_k():
    df = pd.DataFrame({"a": ["x"] * 6 + ["y"] * 3 + ["z"], "b": ["1"] * 10})
    assert sc.own_k(df, ["a", "b"]) == (0.4, 1)


def test_summary_none_scores_and_zero_risk_still_names_attacker():
    card = {**CARD, "utility": [{"id": "H-U2", "description": "LOS", "score": None}],
            "risk_components": {"ed_visits: records with k<5": 0.0, "ed_visits: linkage re-identification": None}}
    md = sc.build_summary(card, BASE, (0.0, 5), ["sex"], "S")
    assert "| H-U2 | LOS | 1.0000 | not evaluated |" in md
    assert "linkage re-identification, was not evaluated" in md
    assert "Attacker model: the toolkit's shipped attackers only" in md and "dictionary attack" in md
    assert "Stronger attackers" in md and "were not tested" in md
