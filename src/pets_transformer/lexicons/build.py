"""Build the detector lexicons from the tuning datasets of the proving ground.

usage: python -m pets_transformer.lexicons.build --root <proving-ground folder>

Only the tuning datasets are read (see results/detect/SPLIT.md); the catalog picks which columns feed which lexicon.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

TUNING = ["finance", "cyber", "education", "mobility", "energy", "smart_city"]
HERE = Path(__file__).parent
# lexicon file -> (catalog subtypes, column-name regex inside those subtypes, split: "value" or min word length)
LEXICONS = {
    "first_names.txt": (["PERSON_NAME"], r"given_name|first_names", 2),
    "last_names.txt": (["PERSON_NAME"], r"surname|last_name", 2),
    "municipalities.txt": (["MUNICIPALITY"], r".", "value"),
    "occupation_words.txt": (["OCCUPATION"], r".", 4),
    "languages.txt": (["LANGUAGE"], r".", "value"),
}


def build(root: Path) -> None:
    cat = pd.read_csv(root / "metadata" / "field_catalog.csv", dtype=str)
    cat = cat[cat.dataset.isin(TUNING)]
    for fname, (subtypes, col_rx, split) in LEXICONS.items():
        rows = cat[cat.subtype.isin(subtypes) & cat.column.str.contains(col_rx)]
        words, sources = set(), []
        for r in rows.itertuples():
            s = pd.read_csv(root / "data" / r.dataset / f"{r.table}.csv", dtype=str, usecols=[r.column])[r.column]
            s = s.dropna().str.strip()
            sources.append(f"data/{r.dataset}/{r.table}.csv:{r.column}")
            for v in s.unique():
                if split == "value":
                    words.add(v.lower())
                else:
                    words.update(w for w in re.findall(r"[^\W\d_]+", v.lower()) if len(w) >= split)
        body = "\n".join(sorted(words))
        (HERE / fname).write_text(f"# source: {', '.join(sources)}\n{body}\n", encoding="utf-8")
        print(f"{fname}: {len(words)} entries from {len(sources)} columns")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    build(Path(ap.parse_args().root))
