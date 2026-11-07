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
    rule, note = pr.resolve("t", "hetu", "non_sensitive", C)
    assert rule["pet"] == "pseudonym" and note == "named rule wins over detected role non_sensitive"


def test_no_note_when_role_is_one_the_rule_expects():
    assert pr.resolve("t", "hetu", "direct_identifier", C)[1] == ""
    k = {"columns": {"t": {"a": {"pet": "keep", "reason": "r"}, "b": {"pet": "age_band", "reason": "r"}}}}
    assert pr.resolve("t", "a", "record_key", k)[1] == "" and pr.resolve("t", "a", "technical_identifier", k)[1] == ""
    assert pr.resolve("t", "a", "quasi_identifier", k)[1] != ""
    assert pr.resolve("t", "b", "quasi_identifier", k)[1] == "" and pr.resolve("t", "b", "direct_identifier", k)[1] != ""


def test_hour_block_param_is_read():
    c = {"columns": {"t": {"id": {"pet": "keep", "reason": "r"}, "ts": {"pet": "hour_of_day", "params": {"block": 3}, "reason": "r"}}},
         "tables": {"t": {"action": "release", "record_id": "id", "reason": "r"}}}
    df = pd.DataFrame({"id": ["1"], "ts": ["2025-03-01 07:30:00"]})
    out, _, _ = pr.protect_table("t", df, c, b"k" * 32, {"ts": "quasi_identifier", "id": "record_key"})
    assert out.ts[0] == "06:00"


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
    assert plan[plan.column == "hetu"].iloc[0].note == ""


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
    (tmp_path / "data" / "unseen" / "u.csv").write_text("a\n1\n")
    monkeypatch.setattr(build, "PG", tmp_path)
    monkeypatch.setattr(build, "BASELINE_DIR", tmp_path / "nobase")
    with pytest.raises(FileNotFoundError, match="raw.json"):
        build.run("HEALTH-S1", out=tmp_path / "o", results=tmp_path / "r", submission=tmp_path / "s")


def test_build_refuses_empty_unseen_folder(tmp_path, monkeypatch):
    from pets_transformer import build
    for d in ("health", "unseen"):
        (tmp_path / "data" / d).mkdir(parents=True)
    monkeypatch.setattr(build, "PG", tmp_path)
    with pytest.raises(FileNotFoundError, match="unseen"):
        build.run("HEALTH-S1", out=tmp_path / "o", results=tmp_path / "r", submission=tmp_path / "s")


def _report(dataset, flags):
    from pets_transformer.detect import PROBS_COLUMNS, DetectReport
    rows = [dict(dataset=dataset, table="t", column=f"c{i}", rule="fallthrough", privacy_role="non_sensitive",
                 subtype="CATEGORY", top1="CATEGORY", p1=0.7, top2="SEX", p2=0.1, top3="LANGUAGE", p3=0.1,
                 decision="needs_review" if f else "confident", flag=f) for i, f in enumerate(flags)]
    probs = pd.DataFrame(rows, columns=PROBS_COLUMNS)
    review = probs[probs.flag != ""].assign(reason="CATEGORY 0.70, SEX 0.10, LANGUAGE 0.10")
    return DetectReport(pd.DataFrame(), probs, review, "hybrid")


def test_report_review_writes_files_and_warns(tmp_path):
    from pets_transformer.build import report_review
    line = report_review([_report("health", ["unclear", ""]), _report("unseen", ["disagree"])], tmp_path)
    assert line.startswith("WARNING: 2 column(s) need review")
    assert "health/t.c0 (unclear)" in line and "unseen/t.c0 (disagree)" in line
    assert len(pd.read_csv(tmp_path / "type_probs.csv", dtype=str)) == 3
    review = pd.read_csv(tmp_path / "needs_review.csv", dtype=str)
    assert list(review.dataset) == ["health", "unseen"] and "reason" in review.columns


def test_report_review_silent_when_clean(tmp_path):
    from pets_transformer.build import report_review
    assert report_review([_report("health", ["", ""])], tmp_path) == ""
    review = pd.read_csv(tmp_path / "needs_review.csv", dtype=str)
    assert review.empty and "flag" in review.columns


def test_cli_build_accepts_semantic_flag(monkeypatch):
    from pets_transformer import build, cli
    seen = {}
    monkeypatch.setattr(build, "run", lambda *a, **kw: seen.update(kw) or [])
    cli.main(["build", "--scenario", "HEALTH-S1", "--semantic", "lexicon"])
    assert seen["semantic"] == "lexicon"
