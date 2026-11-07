"""Calibration: does a stated probability of 0.8 come true 8 times in 10?"""
import numpy as np


def _bins(probs: np.ndarray, y: np.ndarray, bins: int):
    probs, y = np.asarray(probs, float), np.asarray(y)
    conf = probs.max(axis=1)
    hit = (probs.argmax(axis=1) == y).astype(float)
    idx = np.minimum((conf * bins).astype(int), bins - 1)
    return conf, hit, idx


def reliability(probs: np.ndarray, y: np.ndarray, bins: int = 10) -> list[dict]:
    """One row per non-empty confidence bin: bin index, count, mean confidence, accuracy."""
    conf, hit, idx = _bins(probs, y, bins)
    return [{"bin": b, "n": int((idx == b).sum()), "mean_conf": float(conf[idx == b].mean()),
             "accuracy": float(hit[idx == b].mean())} for b in range(bins) if (idx == b).any()]


def ece(probs: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    """Expected calibration error: bin-size-weighted mean gap between confidence and accuracy."""
    n = len(y)
    return float(sum(r["n"] / n * abs(r["accuracy"] - r["mean_conf"]) for r in reliability(probs, y, bins)))
