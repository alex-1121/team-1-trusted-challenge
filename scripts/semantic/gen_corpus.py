"""Training corpus for the column-type model: fake columns per EU locale and type, as JSON lines.

    python scripts/semantic/gen_corpus.py --out data/semantic-corpus --per-type 60 --seed 1000

Writes train.jsonl (training locales), calib.jsonl (CALIB, to fit the temperature) and locked.jsonl (LOCKED, the
test set, read only by evaluate.py), plus hashes.json. Prints the SHA-256 of each file: the same seed and the same
Faker version give the same bytes on any machine, so a teammate can regenerate the corpus and check it against
results/detect-semantic/corpus.json instead of receiving it.

The first line of each file marks it as synthetic; train.py refuses any file without that line. Each next line is
{"locale", "type", "values"}: up to N_VALUES values of one fake column, chosen by features.sample_values exactly as at
run time. Sources: Faker (names, streets, addresses, companies, and towns and jobs where Faker has the locale) and
the committed Featherless word lists in llm_values/<lang>.json. Nothing here reads a real file.
"""
import argparse
import hashlib
import json
import random
import sys
import zlib
from functools import lru_cache
from pathlib import Path

import faker
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from locales import CALIB, LOCALES, LOCKED, lang, languages, stable_faker, train_locales  # noqa: E402,F401

from pets_transformer.semantic.features import sample_values  # noqa: E402
from pets_transformer.semantic.types import TYPES  # noqa: E402

LLM_DIR = Path(__file__).parent / "llm_values"
HEADER = {"corpus": "pets_transformer.semantic", "synthetic": True, "version": 1}
TITLES = ["Dr.", "Dr", "Prof.", "Mr", "Mrs", "Ms", "Ing.", "Mag.", "Hr.", "Fr.", "M.", "Mme", "Sig.", "Sr.", "Sra."]
SEX_EN = {"female": ["female", "F", "woman"], "male": ["male", "M", "man"], "other": ["other", "X"],
          "unknown": ["unknown", "U"]}


def seed_of(*parts) -> int:
    return zlib.crc32("|".join(map(str, parts)).encode())


@lru_cache(maxsize=None)
def faker_for(loc: str) -> "faker.Faker":
    return stable_faker(loc)


@lru_cache(maxsize=None)
def localised(loc: str) -> frozenset:
    """Faker provider kinds (address, job, company, person) that Faker really has for this locale; the others fall
    back to en_US placeholders such as 'Lake Christel' and are not used for town or job columns."""
    out = set()
    for p in faker_for(loc).providers:
        mod = type(p).__module__
        for kind in ("address", "job", "company", "person"):
            if mod.startswith(f"faker.providers.{kind}.") and mod.endswith(loc) and loc != "en_IE":
                out.add(kind)
    return frozenset(out)


@lru_cache(maxsize=None)
def llm(code: str) -> dict:
    p = LLM_DIR / f"{code}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def words(loc: str, kind: str) -> list:
    """The LLM list for the locale's language, else the English one."""
    return llm(lang(loc)).get(kind) or llm("en").get(kind) or []


def case_noise(r: random.Random):
    x = r.random()
    if x < 0.10:
        return str.upper
    if x < 0.17:
        return str.lower
    if x < 0.22:
        return str.title
    return lambda s: s


class Column:
    """One fake column: a pool of distinct values from a type's source, drawn with Zipf-like weights."""

    def __init__(self, loc: str, typ: str, r: random.Random, f: "faker.Faker"):
        self.loc, self.typ, self.r, self.f = loc, typ, r, f

    def pool(self, gen, k: int) -> list:
        vals = []
        for _ in range(k * 4):
            v = gen()
            if v and v not in vals:
                vals.append(v)
            if len(vals) >= k:
                break
        return vals

    def pick(self, xs: list, k: int) -> list:
        xs = sorted(set(xs))
        return self.r.sample(xs, min(k, len(xs)))

    def values(self) -> list:
        r, f, loc = self.r, self.f, self.loc
        t = self.typ
        if t == "PERSON_NAME":
            style = r.choice(["full", "full", "first", "last", "last_first", "titled", "initial"])
            def gen():
                fn, ln = f.first_name(), f.last_name()
                return {"full": f"{fn} {ln}", "first": fn, "last": ln, "last_first": f"{ln}, {fn}",
                        "titled": f"{r.choice(TITLES)} {fn} {ln}" if r.random() < 0.4 else f"{fn} {ln}",
                        "initial": f"{fn[0]}. {ln}"}[style]
            pool = self.pool(gen, r.randint(80, 400))
        elif t == "STREET_ADDRESS":
            full = r.random() < 0.35
            pool = self.pool(lambda: f.address().replace("\n", ", ") if full else f.street_address(),
                             r.randint(80, 400))
        elif t == "MUNICIPALITY":
            towns = words(loc, "towns")
            if "address" in localised(loc):
                towns = towns + self.pool(f.city, 60)
            pool = self.pick(towns, r.randint(5, 80))
        elif t == "LOCATION_NAME":
            src = r.choice(["regions", "countries", "mixed"])
            regions, countries = words(loc, "regions"), words(loc, "countries")
            xs = regions if src == "regions" else countries if src == "countries" else regions + countries
            pool = self.pick(xs, r.randint(4, 40))
        elif t == "ORG_NAME":
            orgs = words(loc, "orgs")
            if "company" in localised(loc) or r.random() < 0.3:
                orgs = orgs + self.pool(f.company, 60)
            pool = self.pick(orgs, r.randint(8, 80))
        elif t == "OCCUPATION":
            jobs = words(loc, "occupations")
            if "job" in localised(loc):
                jobs = jobs + self.pool(f.job, 80)
            pool = self.pick(jobs, r.randint(8, 100))
        elif t == "LANGUAGE":
            if r.random() < 0.3:
                codes = sorted(languages())
                pool = self.pick(codes, r.randint(4, 20))
                if r.random() < 0.5:
                    pool = [c.upper() for c in pool]
            else:
                pool = self.pick(words(loc, "language_names"), r.randint(5, 40))
        elif t == "SEX":
            lists = llm(lang(loc)).get("sex") or SEX_EN
            keys = ["female", "male"] + [k for k in ("other", "unknown") if r.random() < 0.3]
            style = r.random()
            pool = []
            for k in keys:
                opts = sorted(lists.get(k) or SEX_EN[k], key=len)
                pool.append(opts[0] if style < 0.4 else opts[-1] if style < 0.8 else r.choice(opts))
            pool = list(dict.fromkeys(pool))
        elif t == "FREE_TEXT":
            notes = words(loc, "notes")
            def gen():
                parts = r.sample(notes, min(len(notes), r.randint(1, 3))) if notes else [f.sentence()]
                if r.random() < 0.25:
                    parts.insert(r.randint(0, len(parts)), f.name())
                if r.random() < 0.2:
                    parts.append(f.sentence())
                return " ".join(parts)
            pool = self.pool(gen, r.randint(60, 300))
        elif t == "CATEGORY":
            cats = llm(lang(loc)).get("categories") or llm("en").get("categories") or {"status": ["open", "closed"]}
            if r.random() < 0.15:
                cats = llm("en").get("categories") or cats  # English categories appear in every country's data
            group = cats[r.choice(sorted(cats))]
            pool = self.pick(group, r.randint(2, 12))
            if r.random() < 0.15:
                pool = [f"{p} {i}" if r.random() < 0.5 else p for i, p in enumerate(pool)]
        else:
            raise ValueError(t)
        return pool

    def rows(self) -> list:
        pool = self.values()
        if len(pool) < 2:
            return []
        noise = case_noise(self.r)
        a = self.r.uniform(0.0, 1.3)
        w = [1 / (i + 1) ** a for i in range(len(pool))]
        n = self.r.randint(20, 300)
        return [noise(v) for v in self.r.choices(pool, w, k=n)]


def records(split: str, locales: list, per_type: int, seed: int):
    for loc in locales:
        for typ in TYPES:
            f = faker_for(loc)
            f.seed_instance(seed_of(seed, split, loc, typ))
            r = random.Random(seed_of(seed, split, loc, typ, "r"))
            made = 0
            for _ in range(per_type * 3):
                rows = Column(loc, typ, r, f).rows()
                vals = sample_values(pd.Series(rows, dtype=object), seed=0) if rows else []
                if len(vals) >= 5 and len(set(vals)) >= 2:
                    yield {"locale": loc, "type": typ, "values": vals}
                    made += 1
                    if made == per_type:
                        break


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--per-type", type=int, default=60, help="columns per locale and type")
    ap.add_argument("--seed", type=int, default=1000)
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for split, locs in (("train", train_locales()), ("calib", list(CALIB)), ("locked", list(LOCKED))):
        path = a.out / f"{split}.jsonl"
        head = {**HEADER, "split": split, "seed": a.seed, "per_type": a.per_type, "faker": faker.VERSION,
                "llm_values": sorted(p.stem for p in LLM_DIR.glob("*.json"))}
        n = 0
        with path.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(head, ensure_ascii=False, sort_keys=True) + "\n")
            for rec in records(split, locs, a.per_type, a.seed):
                fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
                n += 1
        hashes[split] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "columns": n, "locales": locs}
        print(f"{split}: {n} columns, sha256 {hashes[split]['sha256']}")
    meta = {"seed": a.seed, "per_type": a.per_type, "faker": faker.VERSION, "files": hashes}
    (a.out / "hashes.json").write_text(json.dumps(meta, indent=1, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
