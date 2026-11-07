"""Train the type model's head on a fake corpus written by gen_corpus.py.

The encoder (intfloat/multilingual-e5-small by default) stays frozen. Each column becomes the same feature vector
the detector builds at run time (features.column_vector), a multinomial logistic regression is fitted on
train.jsonl with standardised features, and a temperature is fitted on calib.jsonl (other countries) by minimising
negative log-likelihood over 0.5 to 5.0. locked.jsonl is never read: it is the test set.

Writes to --out: head.npz (W, b, mu, sigma), meta.json (what load_model needs, plus device and corpus hashes) and
train_report.json (per-type F1, temperature, ECE on calib, timing).

Only a corpus made by gen_corpus.py is accepted: its first line must say "synthetic": true, and no path under
data/proving-ground is read. Unique values are encoded once and cached under --cache (default <corpus>/.emb/),
keyed by encoder, revision and the text, so a retrain does not encode again.

    python scripts/semantic/train.py --corpus data/semantic-corpus --out models --revision <sha> --device mps
"""
import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from pets_transformer.semantic.features import (FEATURE_VERSION, MAX_CHARS, N_VALUES,  # noqa: E402
                                                column_vector)
from pets_transformer.semantic.metrics import ece, reliability  # noqa: E402
from pets_transformer.semantic.types import TYPES  # noqa: E402

CORPUS_ID = "pets_transformer.semantic"
SPLITS = ("train", "calib")
STUB_DIM = 32


def refuse(why: str):
    sys.exit(f"not a {CORPUS_ID} corpus: {why}")


def check_corpus(corpus: Path) -> dict:
    """The header line of each split, or exit. Refuses anything that is not a fake corpus from gen_corpus.py."""
    corpus = corpus.resolve()
    parts = corpus.parts
    if any(a == "data" and b == "proving-ground" for a, b in zip(parts, parts[1:])):
        refuse(f"{corpus} is under data/proving-ground")
    headers = {}
    for split in SPLITS:
        p = corpus / f"{split}.jsonl"
        if not p.is_file():
            refuse(f"{p} is missing")
        with p.open(encoding="utf-8") as f:
            first = f.readline()
        try:
            h = json.loads(first)
        except json.JSONDecodeError:
            refuse(f"the first line of {p} is not JSON")
        if not isinstance(h, dict) or h.get("corpus") != CORPUS_ID or h.get("synthetic") is not True:
            refuse(f'the first line of {p} lacks "corpus": "{CORPUS_ID}" and "synthetic": true')
        headers[split] = h
    return headers


def read_split(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        f.readline()
        return [json.loads(line) for line in f if line.strip()]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def stub_encode(texts: list[str]) -> np.ndarray:
    """Test-only encoder: hashed character trigrams, unit length. Needs no torch and no download."""
    out = np.zeros((len(texts), STUB_DIM), np.float32)
    for i, t in enumerate(texts):
        t = f"  {t.lower()} "
        for j in range(len(t) - 2):
            out[i, int(hashlib.md5(t[j:j + 3].encode()).hexdigest(), 16) % STUB_DIM] += 1.0
    n = np.linalg.norm(out, axis=1, keepdims=True)
    return out / np.where(n == 0, 1.0, n)


def pick_device(want: str) -> str:
    if want != "auto":
        return want
    try:
        import torch
    except ImportError:
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class CachedEncoder:
    """Encodes each distinct text once and keeps the vectors on disk (float16) for the next run."""

    def __init__(self, encode, folder: Path | None, batch: int = 4096):
        self.encode_raw, self.folder, self.batch = encode, folder, batch
        self.index: dict[str, int] = {}
        self.vecs: list[np.ndarray] = []
        if folder and (folder / "keys.json").exists():
            keys = json.loads((folder / "keys.json").read_text())
            arr = np.load(folder / "vectors.npy")
            self.index = {k: i for i, k in enumerate(keys)}
            self.vecs = [arr]
            print(f"cache: {len(keys)} vectors from {folder}", flush=True)
        self.stats = {"encoded": 0, "seconds": 0.0}

    @staticmethod
    def key(text: str) -> str:
        return hashlib.sha1(text.encode("utf-8")).hexdigest()

    def _matrix(self) -> np.ndarray:
        if len(self.vecs) > 1:
            self.vecs = [np.concatenate(self.vecs)]
        return self.vecs[0]

    def fill(self, texts: list[str]) -> None:
        todo = list(dict.fromkeys(t for t in texts if self.key(t) not in self.index))
        if not todo:
            return
        print(f"encoding {len(todo)} distinct values ({len(self.index)} cached)", flush=True)
        t0 = time.time()
        for i in range(0, len(todo), self.batch):
            chunk = todo[i:i + self.batch]
            v = np.asarray(self.encode_raw(chunk), np.float32).astype(np.float16)
            base = sum(len(a) for a in self.vecs)
            self.vecs.append(v)
            for j, t in enumerate(chunk):
                self.index[self.key(t)] = base + j
            done = i + len(chunk)
            rate = done / max(time.time() - t0, 1e-9)
            print(f"  {done}/{len(todo)} values, {rate:.0f} values/s, about {(len(todo) - done) / rate / 60:.1f} min left",
                  flush=True)
            if (i // self.batch) % 10 == 9:
                self.save()
        self.stats["encoded"] += len(todo)
        self.stats["seconds"] += time.time() - t0
        self.save()

    def save(self) -> None:
        if not self.folder or not self.vecs:
            return
        self.folder.mkdir(parents=True, exist_ok=True)
        keys = [None] * len(self.index)
        for k, i in self.index.items():
            keys[i] = k
        np.save(self.folder / "vectors.npy", self._matrix())
        (self.folder / "keys.json").write_text(json.dumps(keys))

    def __call__(self, texts: list[str]) -> np.ndarray:
        self.fill(texts)
        m = self._matrix()
        return m[[self.index[self.key(t)] for t in texts]].astype(np.float32)


def features(records: list[dict], enc) -> np.ndarray:
    return np.stack([column_vector(r["values"], enc) for r in records])


def softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def fit_temperature(z: np.ndarray, y: np.ndarray) -> tuple[float, list[dict]]:
    grid = np.round(np.arange(0.5, 5.0001, 0.05), 2)
    nll = [float(-np.log(softmax(z / t)[np.arange(len(y)), y] + 1e-12).mean()) for t in grid]
    best = int(np.argmin(nll))
    return float(grid[best]), [{"t": float(t), "nll": round(v, 5)} for t, v in zip(grid, nll)]


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--encoder", default="intfloat/multilingual-e5-small", help="'stub' is for tests only")
    ap.add_argument("--revision", help="the encoder's pinned commit (required unless --encoder stub)")
    ap.add_argument("--device", default="auto", choices=["auto", "cpu", "mps", "cuda"])
    ap.add_argument("--cache", type=Path, help="default: <corpus>/.emb/")
    ap.add_argument("--C", type=float, default=1.0, help="inverse regularisation strength")
    a = ap.parse_args(argv)

    headers = check_corpus(a.corpus)
    if a.encoder != "stub" and not a.revision:
        ap.error("--revision is required: pin the encoder (see TRAINING.md step 1)")
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, f1_score

    device = "cpu" if a.encoder == "stub" else pick_device(a.device)
    data = {s: read_split(a.corpus / f"{s}.jsonl") for s in SPLITS}
    types = [t for t in TYPES if any(r["type"] == t for r in data["train"])]
    missing = sorted(set(TYPES) - set(types))
    if missing:
        print(f"WARNING: no training columns for {missing}", file=sys.stderr)
    for s in SPLITS:
        data[s] = [r for r in data[s] if r["type"] in types]
        print(f"{s}: {len(data[s])} columns", flush=True)

    if a.encoder == "stub":
        enc = CachedEncoder(stub_encode, None)
    else:
        from pets_transformer.semantic.model import make_encoder
        cache = (a.cache or a.corpus / ".emb") / f"{a.encoder.replace('/', '__')}@{a.revision}"
        enc = CachedEncoder(make_encoder(a.encoder, a.revision, local_files_only=False, device=device), cache)
    print(f"device: {device}", flush=True)
    enc.fill(["query: " + v[:MAX_CHARS] for s in SPLITS for r in data[s] for v in r["values"]])

    t0 = time.time()
    X = {s: features(data[s], enc) for s in SPLITS}
    y = {s: np.array([types.index(r["type"]) for r in data[s]]) for s in SPLITS}
    mu, sigma = X["train"].mean(axis=0), X["train"].std(axis=0)
    sigma = np.where(sigma == 0, 1.0, sigma)
    clf = LogisticRegression(C=a.C, max_iter=3000)
    clf.fit((X["train"] - mu) / sigma, y["train"])
    W = np.zeros((X["train"].shape[1], len(types)))
    b = np.zeros(len(types))
    W[:, clf.classes_] = clf.coef_.T if len(types) > 2 else np.c_[-clf.coef_.T / 2, clf.coef_.T / 2]
    b[clf.classes_] = clf.intercept_ if len(types) > 2 else [-clf.intercept_[0] / 2, clf.intercept_[0] / 2]
    z_calib = ((X["calib"] - mu) / sigma) @ W + b
    temperature, nll_grid = fit_temperature(z_calib, y["calib"])
    p1, pt = softmax(z_calib), softmax(z_calib / temperature)
    pred = pt.argmax(axis=1)
    fit_seconds = time.time() - t0

    a.out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(a.out / "head.npz", W=W.astype(np.float32), b=b.astype(np.float32),
                        mu=mu.astype(np.float32), sigma=sigma.astype(np.float32))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta = {"encoder": a.encoder, "revision": a.revision, "types": types, "temperature": temperature,
            "feature_version": FEATURE_VERSION, "n_values": N_VALUES, "max_chars": MAX_CHARS, "device": device,
            "C": a.C, "created": now,
            "trained_on": {"sha256": {s: sha256(a.corpus / f"{s}.jsonl") for s in SPLITS},
                           "headers": headers,
                           "locales": {s: sorted({r["locale"] for r in data[s]}) for s in SPLITS}}}
    (a.out / "meta.json").write_text(json.dumps(meta, indent=1, sort_keys=True) + "\n")
    f1 = f1_score(y["calib"], pred, labels=range(len(types)), average=None, zero_division=0)
    report = {"created": now, "device": device, "encoder": a.encoder, "revision": a.revision,
              "columns": {s: len(data[s]) for s in SPLITS}, "temperature": temperature,
              "accuracy_calib": round(float(accuracy_score(y["calib"], pred)), 4),
              "macro_f1_calib": round(float(f1.mean()), 4),
              "f1_calib": {t: round(float(v), 4) for t, v in zip(types, f1)},
              "accuracy_train": round(float(clf.score((X["train"] - mu) / sigma, y["train"])), 4),
              "ece_calib": round(ece(pt, y["calib"]), 4), "ece_calib_before_temperature": round(ece(p1, y["calib"]), 4),
              "reliability_calib": reliability(pt, y["calib"]), "nll_by_temperature": nll_grid,
              "encode": {"values": enc.stats["encoded"], "seconds": round(enc.stats["seconds"], 1),
                         "values_per_second": round(enc.stats["encoded"] / enc.stats["seconds"], 1)
                         if enc.stats["seconds"] else None},
              "fit_seconds": round(fit_seconds, 1)}
    (a.out / "train_report.json").write_text(json.dumps(report, indent=1) + "\n")
    print(f"temperature {temperature}; calib accuracy {report['accuracy_calib']}, macro-F1 {report['macro_f1_calib']}, "
          f"ECE {report['ece_calib']} (before temperature {report['ece_calib_before_temperature']})")
    print(f"wrote {a.out}/head.npz, meta.json, train_report.json")


if __name__ == "__main__":
    main()
