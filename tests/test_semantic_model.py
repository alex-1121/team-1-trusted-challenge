"""Features, the model head, the offline loader with its fallback, and calibration metrics.

A stub encoder and a hand-made head stand in for the real encoder, so these tests need neither torch nor a download.
"""
import numpy as np
import pandas as pd
import pytest

from pets_transformer import semantic
from pets_transformer.semantic import model as sm
from pets_transformer.semantic.features import MAX_CHARS, N_SHAPE, column_vector, sample_values, shape_stats
from pets_transformer.semantic.metrics import ece, reliability


def stub(xs):
    return np.stack([np.full(4, len(x) % 7, float) for x in xs])


def head(temperature=1.0):
    rng = np.random.default_rng(0)
    f = 2 * 4 + N_SHAPE
    return sm.TypeModel(stub, rng.normal(size=(f, 3)), rng.normal(size=3), np.zeros(f), np.ones(f),
                        temperature, ("PERSON_NAME", "SEX", "CATEGORY"))


VALUES = ["Anna", "Bert", "Cecilia", "Dmitri", "Eeva", "Anna"]


def test_sample_values_deterministic_and_nonempty():
    s = pd.Series([f"v{i}" for i in range(200)] + ["", "   ", None], dtype=object)
    a, b = sample_values(s), sample_values(s)
    assert a == b and len(a) == 64
    assert all(v.strip() for v in a)
    assert sample_values(pd.Series(["x", "", " y ", None], dtype=object)) == ["x", "y"]


def test_long_values_are_truncated():
    assert len(sample_values(pd.Series(["a" * 5000, "b"]))[0]) == MAX_CHARS


def test_degenerate_column_features_are_finite():
    assert np.isfinite(shape_stats(["a", "a"])).all()
    assert np.isfinite(shape_stats([])).all()
    assert np.isfinite(column_vector(["a", "a"], stub)).all()


def test_column_vector_length():
    assert len(column_vector(VALUES, stub)) == 2 * 4 + N_SHAPE


def test_predict_proba_sums_to_one_and_keys_are_types():
    p = head().predict_proba(VALUES)
    assert set(p) == {"PERSON_NAME", "SEX", "CATEGORY"}
    assert abs(sum(p.values()) - 1.0) < 1e-9


def test_temperature_softens():
    assert max(head(2.0).predict_proba(VALUES).values()) < max(head(1.0).predict_proba(VALUES).values())


def test_tiny_column_returns_none():
    assert head().predict_proba(["a", "b", "c"]) is None
    assert head().predict_proba(["a"] * 10) is None  # one distinct value


def test_unavailable_model_falls_back(tmp_path, monkeypatch, capsys):
    assert sm.load_model(tmp_path) is None
    assert capsys.readouterr().err.count("\n") == 1
    monkeypatch.setattr(semantic, "available", lambda: False)
    assert semantic.resolve_mode("hybrid") == "lexicon"


def test_env_mode_is_read(monkeypatch):
    monkeypatch.setenv("PETS_SEMANTIC", "lexicon")
    assert semantic.resolve_mode(None) == "lexicon"
    with pytest.raises(ValueError):
        semantic.resolve_mode("magic")


def test_ece_perfect_and_bad():
    y = np.array([0, 1, 2, 0])
    assert ece(np.eye(3)[y], y) == 0.0
    probs = np.tile([0.9, 0.1], (100, 1))
    y = np.array([0, 1] * 50)
    assert abs(ece(probs, y) - 0.4) < 1e-9
    rows = reliability(probs, y)
    assert [r["n"] for r in rows] == [100] and abs(rows[0]["accuracy"] - 0.5) < 1e-9
