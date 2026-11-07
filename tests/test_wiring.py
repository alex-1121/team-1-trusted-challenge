import pandas as pd
import pytest

from pets_transformer import protect as pr

C = {
    "columns": {"t": {"hetu": {"pet": "pseudonym", "reason": "keyed"}}},
    "roles": {"t": {"direct_identifier": {"pet": "drop", "reason": "direct"}, "non_sensitive": {"pet": "keep", "reason": "ok"}}},
    "tables": {"t": {"action": "release", "record_id": "id", "reason": "r"}},
}
LABELS = pd.DataFrame({"table": ["t"] * 4, "column": ["id", "hetu", "name", "x"],
                       "privacy_role": ["non_sensitive", "direct_identifier", "direct_identifier", "non_sensitive"]})
DF = pd.DataFrame({"id": ["1", "2"], "hetu": ["a", "b"], "name": ["n1", "n2"], "x": ["u", "v"]})



def test_role_rule_resolves_a_column():
    rule, note = pr.resolve("t", "name", "direct_identifier", C)
    assert rule["pet"] == "drop" and note == ""


def test_named_rule_wins_and_sets_note():
    rule, note = pr.resolve("t", "hetu", "direct_identifier", C)
    assert rule["pet"] == "pseudonym" and note == "named rule wins over detected role direct_identifier"


def test_unlabelled_unnamed_column_raises():
    with pytest.raises(ValueError, match="mystery"):
        pr.resolve("t", "mystery", "", C)


def test_table_missing_from_contract_is_listed(tmp_path):
    orig = tmp_path / "health"
    orig.mkdir()
    DF.to_csv(orig / "t.csv", index=False)
    DF.to_csv(orig / "extra.csv", index=False)
    plan = pr.protect_folder(C, orig, tmp_path / "out", b"k" * 32, LABELS)
    row = plan[plan.table == "extra"].iloc[0]
    assert row.pet == "not released" and row.reason == "not in contract, not released"
    assert not (tmp_path / "out" / "extra.csv").exists()
    assert plan[plan.column == "hetu"].iloc[0].note.startswith("named rule wins")


def test_every_taxonomy_role_resolves_in_health_contract():
    from pathlib import Path
    from pets_transformer import contract as ct
    c = ct.load(Path(__file__).parent.parent / "contracts" / "HEALTH-S1.json")
    roles = ["direct_identifier", "quasi_identifier", "sensitive_attribute", "technical_identifier",
             "free_text", "record_key", "non_sensitive"]
    for t, spec in c["tables"].items():
        if spec["action"] == "release":
            for r in roles:
                pr.resolve(t, "unnamed_col", r, c)
    assert pr.resolve("ed_visits", "unnamed_col", "quasi_identifier", c)[0]["pet"] == "drop"


def test_build_refuses_missing_unseen_folder(tmp_path, monkeypatch):
    from pets_transformer import build
    (tmp_path / "data" / "health").mkdir(parents=True)
    monkeypatch.setattr(build, "PG", tmp_path)
    with pytest.raises(FileNotFoundError, match="unseen"):
        build.run("HEALTH-S1", out=tmp_path / "o", results=tmp_path / "r", submission=tmp_path / "s")
    assert not (tmp_path / "s").exists()


def test_build_refuses_missing_baseline(tmp_path, monkeypatch):
    from pets_transformer import build
    for d in ("health", "unseen"):
        (tmp_path / "data" / d).mkdir(parents=True)
    monkeypatch.setattr(build, "PG", tmp_path)
    monkeypatch.setattr(build, "BASELINE_DIR", tmp_path / "nobase")
    with pytest.raises(FileNotFoundError, match="raw.json"):
        build.run("HEALTH-S1", out=tmp_path / "o", results=tmp_path / "r", submission=tmp_path / "s")
