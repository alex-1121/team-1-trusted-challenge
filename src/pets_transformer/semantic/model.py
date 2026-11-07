"""The type model: a frozen multilingual sentence encoder plus a small committed classifier head.

At run time the encoder loads from the local cache only (local_files_only=True), so processing never touches the
network. `python -m pets_transformer.semantic.model --download` is the one explicit network call that fills the
cache. Without the `semantic` extra, the head files or the cached encoder, load_model returns None and prints one
warning line; the detector then runs on word lists only.
"""
import argparse
import functools
import json
import sys
from pathlib import Path

import numpy as np

from .features import FEATURE_VERSION, column_vector

MODEL_DIR = Path(__file__).parent / "models"
MIN_VALUES = 5


def make_encoder(name: str, revision: str, local_files_only: bool = True, device: str | None = None):
    """encode(texts) -> (n, D) float32 unit vectors. Shared by run time and training so both encode alike."""
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(name, revision=revision, local_files_only=local_files_only, device=device)

    def encode(texts: list[str]) -> np.ndarray:
        return np.asarray(m.encode(texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False),
                          dtype=np.float32)
    return encode


class TypeModel:
    def __init__(self, encode, W: np.ndarray, b: np.ndarray, mu: np.ndarray, sigma: np.ndarray,
                 temperature: float, types: tuple[str, ...]):
        self.encode, self.W, self.b, self.mu = encode, W, b, mu
        self.sigma = np.where(sigma == 0, 1.0, sigma)
        self.temperature, self.types = float(temperature), tuple(types)

    def predict_proba(self, values: list[str]) -> dict[str, float] | None:
        """Type probabilities for a column's values, or None when there are too few to judge."""
        if len(values) < MIN_VALUES or len(set(values)) < 2:
            return None
        x = (column_vector(values, self.encode) - self.mu) / self.sigma
        z = (x @ self.W + self.b) / self.temperature
        p = np.exp(z - z.max())
        p /= p.sum()
        return {t: float(q) for t, q in zip(self.types, p)}


def _warn(why: str) -> None:
    print(f"WARNING: semantic model unavailable ({why}); detecting with word lists only (lexicon).", file=sys.stderr)


@functools.lru_cache(maxsize=None)
def load_model(model_dir: Path = MODEL_DIR) -> TypeModel | None:
    model_dir = Path(model_dir)
    if not (model_dir / "head.npz").exists() or not (model_dir / "meta.json").exists():
        _warn(f"no trained head in {model_dir}")
        return None
    meta = json.loads((model_dir / "meta.json").read_text())
    if meta.get("feature_version") != FEATURE_VERSION:
        _warn(f"head has feature_version {meta.get('feature_version')}, code has {FEATURE_VERSION}")
        return None
    try:
        encode = make_encoder(meta["encoder"], meta["revision"])
    except ImportError:
        _warn("the 'semantic' extra is not installed: pip install -e .[semantic]")
        return None
    except Exception as e:  # missing from the local cache, or a broken cache
        _warn(f"encoder {meta['encoder']} not in the local cache ({type(e).__name__}); "
              "run python -m pets_transformer.semantic.model --download")
        return None
    h = np.load(model_dir / "head.npz")
    return TypeModel(encode, h["W"], h["b"], h["mu"], h["sigma"], meta["temperature"], tuple(meta["types"]))


def available() -> bool:
    return load_model() is not None


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Fetch the encoder at its pinned revision into the local cache.")
    ap.add_argument("--download", action="store_true", required=True)
    ap.add_argument("--encoder", help="default: from models/meta.json")
    ap.add_argument("--revision", help="default: from models/meta.json")
    a = ap.parse_args(argv)
    meta_path = MODEL_DIR / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    name, rev = a.encoder or meta.get("encoder"), a.revision or meta.get("revision")
    if not name or not rev:
        sys.exit("no trained head yet: pass --encoder and --revision")
    make_encoder(name, rev, local_files_only=False)
    print(f"cached {name} at revision {rev}")


if __name__ == "__main__":
    main()
