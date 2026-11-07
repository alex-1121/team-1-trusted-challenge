"""Column features shared by training and run time: a sample of values, their encoder embeddings, and shape stats.

The same code builds the vector in scripts/semantic/train.py and in the detector, so a trained head always sees
the features it was trained on. FEATURE_VERSION is written into meta.json; change it whenever this file changes
what a vector means, and retrain.
"""
import string
import unicodedata
from collections import Counter
from typing import Callable

import numpy as np
import pandas as pd

N_VALUES = 64
MAX_CHARS = 256
N_SHAPE = 20
FEATURE_VERSION = 1
PUNCT = set(string.punctuation)


def sample_values(s: pd.Series, n: int = N_VALUES, seed: int = 0) -> list[str]:
    """Non-empty stripped values, at most n, sampled without replacement with a fixed seed, each cut to MAX_CHARS."""
    v = s.dropna().astype(str).str.strip()
    v = v[v != ""]
    if len(v) > n:
        v = v.sample(n, random_state=seed)
    return [x[:MAX_CHARS] for x in v]


def _frac(x: str, pred) -> float:
    return sum(map(pred, x)) / len(x) if x else 0.0


def _non_ascii_letter(c: str) -> bool:
    return ord(c) > 127 and unicodedata.category(c).startswith("L")


def shape_stats(values: list[str]) -> np.ndarray:
    """N_SHAPE numbers describing how the values look. Always finite, also for an empty or one-value list."""
    if not values:
        return np.zeros(N_SHAPE)
    lens = np.array([len(x) for x in values], float)
    toks = [x.split() for x in values]
    ntok = np.array([len(t) for t in toks], float)
    tok_len = np.array([np.mean([len(w) for w in t]) if t else 0.0 for t in toks])
    digit = np.array([_frac(x, str.isdigit) for x in values])
    punct = np.array([_frac(x, PUNCT.__contains__) for x in values])
    nonascii = np.array([_frac(x, _non_ascii_letter) for x in values])
    counts = Counter(values)
    share = lambda pred: float(np.mean([bool(pred(x)) for x in values]))  # noqa: E731
    out = np.array([
        lens.mean(), lens.std(), ntok.mean(), ntok.std(), tok_len.mean(),
        share(lambda x: x[:1].isupper()), share(str.isupper), share(str.islower),
        digit.mean(), digit.std(), share(lambda x: any(c.isdigit() for c in x)),
        punct.mean(), share(lambda x: "," in x), share(lambda x: "-" in x),
        nonascii.mean(), share(lambda x: any(map(_non_ascii_letter, x))),
        len(counts) / len(values), counts.most_common(1)[0][1] / len(values), np.log1p(len(counts)),
        share(lambda x: len(x.split()) >= 2),
    ], float)
    return np.nan_to_num(out)


def column_vector(values: list[str], encode: Callable[[list[str]], np.ndarray]) -> np.ndarray:
    """concat(mean of embeddings, their spread, shape stats): length 2*D + N_SHAPE."""
    values = [x[:MAX_CHARS] for x in values]
    e = np.asarray(encode(["query: " + x for x in values]), float)
    return np.concatenate([e.mean(axis=0), e.std(axis=0), shape_stats(values)])
