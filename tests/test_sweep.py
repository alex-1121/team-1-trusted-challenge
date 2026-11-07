import pandas as pd

from pets_transformer import pets
from pets_transformer.sweep import choose

TS = pd.Series(["2026-01-01T00:30:00", "2026-01-01T05:10:00", "2026-01-01T23:59:00", None])


def test_hour_block():
    assert pets.hour_of_day(TS).iloc[:3].tolist() == ["00:00", "05:00", "23:00"]
    assert pets.hour_of_day(TS, block=2).iloc[:3].tolist() == ["00:00", "04:00", "22:00"]
    assert pets.hour_of_day(TS, block=3).iloc[:3].tolist() == ["00:00", "03:00", "21:00"]
    assert pd.isna(pets.hour_of_day(TS, block=3).iloc[3])


def _r(cell, comp, own, u2=1.0):
    return {"cell": cell, "tasks": {"H-U2": u2}, "own_k": own, "composite": comp}


def test_choose_prefers_k_target_then_composite():
    rows = [_r("a", 0.95, 0.08), _r("b", 0.93, 0.04), _r("c", 0.92, 0.03), _r("d", 0.99, 0.01, u2=0.5)]
    assert choose(rows, ["H-U2"])["cell"] == "b"


def test_choose_fallback_lowest_k_among_best_composite():
    rows = [_r("a", 0.95001, 0.08), _r("b", 0.95004, 0.06), _r("c", 0.90, 0.07)]
    assert choose(rows, ["H-U2"])["cell"] == "b"
