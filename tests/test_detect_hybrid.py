"""Hybrid detection: the word-list label stands, the model labels the fall-through, disagreements are listed.

A stub model stands in for the encoder and head: it answers by which known name set a column's values come from.
It goes through TypeModel's real gate (too few values -> no answer).
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pets_transformer import detect
from pets_transformer.detect import MAX_ROWS, classify, classify_traced, detect_dataset, detect_dataset_report
from pets_transformer.semantic import ModelUnavailable
from pets_transformer.semantic.model import TypeModel
from pets_transformer.semantic.types import TYPES

DE = ["Siegfried Hoffmeister", "Gertrud Schwarzkopf", "Wolfgang Brandauer", "Hildegard Kesselring",
      "Reinhold Ostermeyer", "Brunhilde Zimmerling", "Ottokar Feuerbach", "Waltraud Eisenhut"]
FI = ["Matti Virtanen", "Liisa Korhonen", "Juha Nieminen", "Aino Mäkinen", "Pekka Hämäläinen", "Sanna Laine",
      "Ville Heikkinen", "Kaisa Koskinen"]
TOWNS = ["Naantali", "Lieto", "Masku", "Loimaa", "Laitila", "Kaarina"]
N = 80


def probs(**kw):
    p = dict.fromkeys(TYPES, 0.0)
    p.update(kw)
    return p


class Stub(TypeModel):
    def __init__(self):
        super().__init__(None, np.zeros((1, 1)), np.zeros(1), np.zeros(1), np.ones(1), 1.0, TYPES)
        self.calls = 0
        self.answer = None

    def _proba(self, values):
        self.calls += 1
        if self.answer is not None:
            return self.answer(values)
        if set(values) <= set(DE):
            return probs(PERSON_NAME=0.9, CATEGORY=0.1)
        if set(values) <= set(FI):
            return probs(CATEGORY=0.95, PERSON_NAME=0.05)
        return None


@pytest.fixture
def stub(monkeypatch):
    s = Stub()
    monkeypatch.setattr(detect, "load_model", lambda: s)
    return s


def cyc(xs, n=N):
    return [xs[i % len(xs)] for i in range(n)]


@pytest.fixture
def tables(tmp_path):
    pd.DataFrame({"id": [f"SR-2024-{i + 1:06d}" for i in range(N)], "de_name": cyc(DE), "fi_name": cyc(FI),
                  "state": cyc(["open", "closed", "pending"]),
                  "few": DE[:3] + [""] * (N - 3)}).to_csv(tmp_path / "people.csv", index=False)
    return tmp_path


def rows(report, column):
    return report.type_probs[report.type_probs.column == column]


def lab(report, column):
    r = report.labels.set_index("column").loc[column]
    return r.privacy_role, r.subtype


def test_classify_traced_tags():
    assert classify_traced(pd.Series(["131052-308T"] * 20))[3] == "pre"
    assert classify_traced(pd.Series(cyc(FI)))[3] == "lex_name"
    assert classify_traced(pd.Series(cyc(["foo", "bar", "baz"])))[3] == "fallthrough"
    assert classify_traced(pd.Series([str(i) for i in range(50)]))[3] == "numeric"
    s = pd.Series(cyc(FI))
    assert classify(s) == classify_traced(s)[:3]


def test_lexicon_mode_equals_today(tables, stub):
    report = detect_dataset_report(tables, "x", "lexicon")
    df = pd.read_csv(tables / "people.csv", dtype=str)
    for c in df.columns:
        assert lab(report, c) == classify(df[c])[:2]
    assert report.mode == "lexicon" and report.type_probs.empty and stub.calls == 0
    assert detect_dataset(tables, "x", "lexicon").equals(report.labels)


def test_fallthrough_column_gets_model_label(tables, stub):
    report = detect_dataset_report(tables, "x", "hybrid")
    assert report.mode == "hybrid"
    assert lab(report, "de_name") == ("direct_identifier", "PERSON_NAME")
    assert rows(report, "de_name").iloc[0][["rule", "top1", "decision"]].tolist() == [
        "fallthrough", "PERSON_NAME", "confident"]


def test_lexicon_hit_kept_and_disagreement_listed(tables, stub):
    report = detect_dataset_report(tables, "x", "hybrid")
    assert lab(report, "fi_name") == ("direct_identifier", "PERSON_NAME")
    nr = report.needs_review.set_index("column")
    assert list(nr.index) == ["fi_name"] and nr.at["fi_name", "flag"] == "disagree"
    assert "CATEGORY 0.95" in nr.at["fi_name", "reason"]


def test_tiny_column_skips_model(tables, stub):
    report = detect_dataset_report(tables, "x", "hybrid")
    assert rows(report, "few").empty
    assert lab(report, "few") == ("non_sensitive", "CATEGORY")


def test_wide_sample_path_uses_same_combine(tmp_path, stub):
    n = MAX_ROWS + 200
    late = [""] * MAX_ROWS + cyc(DE, 200)
    pd.DataFrame({"k": cyc(["a", "b", "c"], n), "late": late}).to_csv(tmp_path / "t.csv", index=False)
    report = detect_dataset_report(tmp_path, "x", "hybrid")
    assert lab(report, "late") == ("direct_identifier", "PERSON_NAME")
    assert rows(report, "late").iloc[0]["top1"] == "PERSON_NAME"


def test_outputs_hold_no_values(tables, stub, capsys):
    out, rev = tables / "o" / "labels.csv", tables / "rev"
    detect.main(["--data", str(tables), "--dataset", "x", "--out", str(out), "--semantic", "hybrid",
                 "--review-dir", str(rev)])
    assert sorted(p.name for p in (tables / "o").iterdir()) == ["labels.csv"]  # nothing beside the labels
    tp = (rev / "labels_type_probs.csv").read_text()
    nr = (rev / "labels_needs_review.csv").read_text()
    assert len(tp.splitlines()) >= 3 and len(nr.splitlines()) == 2
    values = {v for v in pd.read_csv(tables / "people.csv", dtype=str).fillna("").stack() if v.strip()}
    assert values and not [v for v in values if v in tp or v in nr]
    assert "WARNING: 1 column(s) need review: people.fi_name (disagree)" in capsys.readouterr().out


def test_requested_mode_without_model_fails_default_falls_back(tables, monkeypatch):
    monkeypatch.setattr(detect, "load_model", lambda: None)
    for mode in ("hybrid", "advisor"):
        with pytest.raises(ModelUnavailable):
            detect_dataset_report(tables, "x", mode)
    monkeypatch.delenv("PETS_SEMANTIC")
    report = detect_dataset_report(tables, "x")
    assert report.mode == "lexicon"
    assert report.labels.equals(detect_dataset_report(tables, "x", "lexicon").labels)


def test_lexicon_writes_no_review_files(tables, stub):
    out, rev = tables / "o" / "labels.csv", tables / "rev"
    detect.main(["--data", str(tables), "--dataset", "x", "--out", str(out), "--semantic", "lexicon",
                 "--review-dir", str(rev)])
    assert not rev.exists() and sorted(p.name for p in (tables / "o").iterdir()) == ["labels.csv"]


def test_labels_only_skips_model_unless_hybrid(tables, stub, monkeypatch):
    monkeypatch.delenv("PETS_SEMANTIC")  # default: advisor, which never changes a label
    assert detect_dataset(tables, "x").equals(detect_dataset_report(tables, "x", "lexicon").labels)
    assert stub.calls == 0  # select and protect without --labels do not load or run the model
    detect_dataset(tables, "x", "hybrid")
    assert stub.calls > 0


def test_hybrid_wide_look_never_less_protective_than_lexicon(tmp_path, stub):
    # first MAX_ROWS rows: a harmless word the model would call an occupation; later rows: Finnish names, which the
    # word lists catch only on the wide sample. Hybrid must not stop at the model's quasi-identifier.
    n = MAX_ROWS * 10  # the wide sample is then 90% names
    col = cyc(["foo", "bar", "baz"], MAX_ROWS) + cyc(FI, n - MAX_ROWS)
    pd.DataFrame({"k": cyc(["a", "b", "c"], n), "who": col}).to_csv(tmp_path / "t.csv", index=False)
    stub.answer = lambda values: probs(OCCUPATION=0.9, CATEGORY=0.1) if not set(values) & set(FI) else None
    lex = lab(detect_dataset_report(tmp_path, "x", "lexicon"), "who")
    hyb = lab(detect_dataset_report(tmp_path, "x", "hybrid"), "who")
    assert lex == ("direct_identifier", "PERSON_NAME") and hyb == lex
    assert stub.calls == 2  # one model read per column (k and who), not one per look


def test_moot_flag_on_table_without_person_is_dropped(tmp_path, stub):
    # a stops-like reference table: no person column; the model would call a harmless column a town (quasi), which
    # the reference-table rule demotes to non-sensitive anyway, so no flag. A model-said name keeps its flag.
    pd.DataFrame({"zone": cyc(["foo", "bar", "baz", "qux", "quux"]), "state": cyc(["open", "closed", "pending"])}
                 ).to_csv(tmp_path / "stops.csv", index=False)
    stub.answer = lambda values: probs(MUNICIPALITY=0.9, CATEGORY=0.1) if "foo" in values else None
    rep = detect_dataset_report(tmp_path, "x", "advisor")
    assert rows(rep, "zone").iloc[0]["flag"] == "" and rep.needs_review.empty
    stub.answer = lambda values: probs(PERSON_NAME=0.9, CATEGORY=0.1) if "foo" in values else None
    rep = detect_dataset_report(tmp_path, "x", "advisor")
    assert list(rep.needs_review.column) == ["zone"]


def test_person_table_flip_is_protective(tmp_path, stub):
    pd.DataFrame({"town": cyc(TOWNS), "who": cyc(DE)}).to_csv(tmp_path / "visits.csv", index=False)
    assert lab(detect_dataset_report(tmp_path, "x", "lexicon"), "town")[0] == "non_sensitive"
    assert lab(detect_dataset_report(tmp_path, "x", "hybrid"), "town") == ("quasi_identifier", "MUNICIPALITY")


def test_empty_dataset_still_gives_a_report(tmp_path):
    (tmp_path / "nothing").mkdir()
    report = detect.detect_dataset_report(tmp_path, "nothing", "lexicon")
    assert isinstance(report, detect.DetectReport)
    assert report.labels.empty and report.type_probs.empty and report.needs_review.empty


def test_advisor_keeps_word_list_labels_and_flags_model_suggestion(tables, stub):
    report = detect_dataset_report(tables, "x", "advisor")
    lexicon = detect_dataset_report(tables, "x", "lexicon")
    assert report.mode == "advisor" and report.labels.equals(lexicon.labels)
    assert lab(report, "de_name") == ("non_sensitive", "CATEGORY")  # the model's PERSON_NAME is only a suggestion
    flagged = report.needs_review.set_index("column")
    assert flagged.loc["de_name", "flag"] == "suggest"
    assert "model suggests direct_identifier PERSON_NAME" in flagged.loc["de_name", "reason"]
    assert flagged.loc["fi_name", "flag"] == "disagree"  # word-list hit, model says CATEGORY 0.95


def test_default_with_model_is_advisor(tables, stub, monkeypatch):
    monkeypatch.delenv("PETS_SEMANTIC")
    report = detect_dataset_report(tables, "x")
    assert report.mode == "advisor"
    assert report.labels.equals(detect_dataset_report(tables, "x", "lexicon").labels)


def test_non_escalating_wide_reading_does_not_change_the_label(tmp_path, monkeypatch):
    """A wide second look that reads another, non-escalating role (here a record id) never sets the label."""
    n = MAX_ROWS * 10  # the wide sample is then 90% ids
    head = cyc(["open", "closed", "pending"], MAX_ROWS)
    tail = [f"REQ-{i:08d}" for i in range(n - MAX_ROWS)]
    pd.DataFrame({"state": head + tail}).to_csv(tmp_path / "t.csv", index=False)
    s = Stub()
    s.answer = lambda values: probs(CATEGORY=0.9, OCCUPATION=0.1)
    monkeypatch.setattr(detect, "load_model", lambda: s)
    lex = detect_dataset_report(tmp_path, "x", "lexicon")
    hyb = detect_dataset_report(tmp_path, "x", "hybrid")
    assert lab(hyb, "state") == lab(lex, "state")
