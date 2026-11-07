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
