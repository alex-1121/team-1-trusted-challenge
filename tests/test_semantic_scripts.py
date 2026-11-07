"""Generators under scripts/semantic/: fake EU test tables and the training corpus (fake data only)."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("faker")

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "semantic"
sys.path.insert(0, str(SCRIPTS))

from pets_transformer.semantic.features import N_VALUES  # noqa: E402
from pets_transformer.semantic.types import TYPES  # noqa: E402


def run(script, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True,
                          cwd=ROOT, check=True)


def test_locked_locales_never_in_training():
    import gen_corpus
    train = set(gen_corpus.train_locales())
    assert train & set(gen_corpus.LOCKED) == set()
    assert train & set(gen_corpus.CALIB) == set()
    held_out_langs = {gen_corpus.lang(loc) for loc in gen_corpus.LOCKED + gen_corpus.CALIB}
    assert not {gen_corpus.lang(loc) for loc in train} & held_out_langs


@pytest.fixture(scope="module")
def corpus(tmp_path_factory):
    out = tmp_path_factory.mktemp("corpus")
    res = run("gen_corpus.py", "--out", out, "--per-type", 2, "--seed", 5)
    return out, res.stdout


def test_corpus_header_and_schema(corpus):
    out, _ = corpus
    for split in ("train", "calib", "locked"):
        lines = (out / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()
        head = json.loads(lines[0])
        assert head["corpus"] == "pets_transformer.semantic" and head["synthetic"] is True and head["split"] == split
        recs = [json.loads(x) for x in lines[1:]]
        assert {r["type"] for r in recs} == set(TYPES)
        assert all(1 <= len(r["values"]) <= N_VALUES and all(isinstance(v, str) for v in r["values"]) for r in recs)


def test_corpus_prints_hashes_and_is_deterministic(corpus, tmp_path):
    out, stdout = corpus
    digest = hashlib.sha256((out / "train.jsonl").read_bytes()).hexdigest()
    assert digest in stdout
    run("gen_corpus.py", "--out", tmp_path, "--per-type", 2, "--seed", 5)
    assert (tmp_path / "train.jsonl").read_bytes() == (out / "train.jsonl").read_bytes()


def test_dev_tables_deterministic(tmp_path):
    run("gen_eu_tables.py", "--out", tmp_path / "a", "--split", "dev", "--rows", 300)
    run("gen_eu_tables.py", "--out", tmp_path / "b", "--split", "dev", "--rows", 300)
    a = (tmp_path / "a" / "de_DE" / "customers.csv").read_bytes()
    assert a == (tmp_path / "b" / "de_DE" / "customers.csv").read_bytes()
    assert (tmp_path / "a" / "mixed_EU" / "customers.csv").exists()


def test_catalog_matches_columns(tmp_path):
    run("gen_eu_tables.py", "--out", tmp_path, "--split", "locked", "--rows", 200)
    cat = pd.read_csv(tmp_path / "catalog.csv", dtype=str)
    assert set(cat.dataset) == {"cs_CZ", "pt_PT", "hu_HU"}
    for ds, g in cat.groupby("dataset"):
        cols = pd.read_csv(tmp_path / ds / "customers.csv", dtype=str, nrows=1).columns
        assert set(g.column) == set(cols)


# Task 6: train.py

def _write_corpus(d: Path, header: dict | None, records: list[dict]) -> None:
    d.mkdir(parents=True, exist_ok=True)
    for split in ("train", "calib"):
        lines = ([json.dumps(header | {"split": split})] if header is not None else []) + [json.dumps(r) for r in records]
        (d / f"{split}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _train(*args):
    return subprocess.run([sys.executable, str(SCRIPTS / "train.py"), *map(str, args)], capture_output=True,
                          text=True, cwd=ROOT)


TOY = [{"locale": "xx_XX", "type": t, "values": vals} for t, vals in [
    ("PERSON_NAME", ["Anna Berg", "Otto Lind", "Mia Koski", "Eero Salo", "Liisa Aho", "Kari Mäki"]),
    ("PERSON_NAME", ["Jan Novak", "Eva Horn", "Ida Vik", "Per Dahl", "Ole Moe", "Siv Lie"]),
    ("SEX", ["F", "M", "F", "F", "M", "M", "F"]),
    ("SEX", ["female", "male", "male", "female", "female", "male"]),
    ("CATEGORY", ["open", "closed", "pending", "open", "open", "closed"]),
    ("CATEGORY", ["low", "high", "medium", "low", "low", "high"]),
]]
HEADER = {"corpus": "pets_transformer.semantic", "synthetic": True, "version": 1}


def test_train_refuses_non_corpus_input(tmp_path):
    pytest.importorskip("sklearn")
    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()
    (csv_dir / "people.csv").write_text("name\nAnna Berg\n")
    no_flag = tmp_path / "noflag"
    _write_corpus(no_flag, {"corpus": "pets_transformer.semantic", "version": 1}, TOY)
    pg = tmp_path / "data" / "proving-ground" / "health"
    _write_corpus(pg, HEADER, TOY)
    for d in (csv_dir, no_flag, pg):
        r = _train("--corpus", d, "--out", tmp_path / "m", "--encoder", "stub")
        assert r.returncode != 0, d
        assert "not a pets_transformer.semantic corpus" in r.stderr, (d, r.stderr)
    assert not (tmp_path / "m" / "head.npz").exists()


def test_train_roundtrip_with_stub_encoder(tmp_path):
    pytest.importorskip("sklearn")
    import numpy as np
    from pets_transformer.semantic.model import TypeModel
    from train import stub_encode
    corpus = tmp_path / "corpus"
    _write_corpus(corpus, HEADER, TOY)
    r = _train("--corpus", corpus, "--out", tmp_path / "m", "--encoder", "stub", "--device", "cpu")
    assert r.returncode == 0, r.stderr
    meta = json.loads((tmp_path / "m" / "meta.json").read_text())
    report = json.loads((tmp_path / "m" / "train_report.json").read_text())
    assert set(meta["types"]) == {"PERSON_NAME", "SEX", "CATEGORY"}
    assert meta["device"] == "cpu" and set(meta["trained_on"]["sha256"]) == {"train", "calib"}
    assert 0.5 <= report["temperature"] <= 5.0 and "ece_calib" in report and "f1_calib" in report
    h = np.load(tmp_path / "m" / "head.npz")
    m = TypeModel(stub_encode, h["W"], h["b"], h["mu"], h["sigma"], meta["temperature"], tuple(meta["types"]))
    for rec in TOY:
        p = m.predict_proba(rec["values"])
        assert max(p, key=p.get) == rec["type"], (rec["type"], p)


def test_pick_device_cpu_without_torch_accelerators():
    from train import pick_device
    assert pick_device("cpu") == "cpu"
    assert pick_device("auto") in {"cpu", "cuda", "mps"}
