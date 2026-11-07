"""Fake EU test tables: one labelled 'customers' table per locale, plus catalog.csv in the proving-ground format.

    python scripts/semantic/gen_eu_tables.py --out data/semantic-eval/dev --split dev
    python scripts/semantic/gen_eu_tables.py --out data/semantic-eval/locked --split locked

dev: 8 locales (seed 7) plus mixed_EU, whose name, town and occupation columns draw from all 8.
locked: cs_CZ, pt_PT, hu_HU (seed 99); never used for training or tuning, run once (results/detect-semantic/SPLIT.md).
Everything is made by Faker; no real person's data. Dates are fixed, so the same Faker version gives the same files.
"""
import argparse
import random
import string
from datetime import datetime
from pathlib import Path

import pandas as pd
from locales import stable_faker

DEV = ["fi_FI", "de_DE", "fr_FR", "pl_PL", "it_IT", "es_ES", "nl_NL", "sv_SE"]
LOCKED = ["cs_CZ", "pt_PT", "hu_HU"]
SEEDS = {"dev": 7, "locked": 99}
SEX = {"fi_FI": ("nainen", "mies"), "de_DE": ("weiblich", "männlich"), "fr_FR": ("femme", "homme"),
       "pl_PL": ("kobieta", "mężczyzna"), "it_IT": ("femmina", "maschio"), "es_ES": ("mujer", "hombre"),
       "nl_NL": ("vrouw", "man"), "sv_SE": ("kvinna", "man"), "cs_CZ": ("žena", "muž"),
       "pt_PT": ("feminino", "masculino"), "hu_HU": ("nő", "férfi")}
DATEFMT = {"fi_FI": "%d.%m.%Y", "de_DE": "%d.%m.%Y", "pl_PL": "%d.%m.%Y", "fr_FR": "%d/%m/%Y", "it_IT": "%d/%m/%Y",
           "es_ES": "%d/%m/%Y", "nl_NL": "%d-%m-%Y", "sv_SE": "%Y-%m-%d", "cs_CZ": "%d.%m.%Y", "pt_PT": "%d/%m/%Y",
           "hu_HU": "%Y.%m.%d."}
PLANS = ["Basic", "Plus", "Premium", "Family"]

LABELS = [  # column, role, subtype
    ("customer_id", "record_key", "RECORD_ID"),
    ("full_name", "direct_identifier", "PERSON_NAME"),
    ("first_name", "direct_identifier", "PERSON_NAME"),
    ("last_name", "direct_identifier", "PERSON_NAME"),
    ("email", "direct_identifier", "EMAIL"),
    ("phone", "direct_identifier", "PHONE"),
    ("national_id", "direct_identifier", "NATIONAL_ID"),
    ("iban", "direct_identifier", "IBAN"),
    ("street_address", "direct_identifier", "STREET_ADDRESS"),
    ("full_address", "direct_identifier", "STREET_ADDRESS"),
    ("licence_plate", "direct_identifier", "LICENSE_PLATE"),
    ("postcode", "quasi_identifier", "POSTCODE"),
    ("city", "quasi_identifier", "MUNICIPALITY"),
    ("birth_date", "quasi_identifier", "BIRTH_DATE"),
    ("sex", "quasi_identifier", "SEX"),
    ("occupation", "quasi_identifier", "OCCUPATION"),
    ("employer", "quasi_identifier", "ORG_NAME"),
    ("signup_ts", "quasi_identifier", "TIMESTAMP"),
    ("last_login_ip", "technical_identifier", "IP_ADDRESS"),
    ("support_note", "free_text", "FREE_TEXT"),
    ("plan", "non_sensitive", "CATEGORY"),
    ("items_in_cart", "non_sensitive", "MEASUREMENT"),
]


def iban(cc, bban):
    num = "".join(str(int(ch, 36)) for ch in bban + cc + "00")
    return f"{cc}{98 - int(num) % 97:02d}{bban}"


def de_idnr(r):
    """Steuer-IdNr: 10 digits, first not 0, exactly one digit twice, then the ISO 7064 MOD 11,10 check digit."""
    while True:
        d = [r.randint(1, 9)] + [r.randint(0, 9) for _ in range(9)]
        counts = {x: d.count(x) for x in d}
        if max(counts.values()) == 2 and list(counts.values()).count(2) == 1:
            break
    p = 10
    for x in d:
        s = (x + p) % 10 or 10
        p = (2 * s) % 11
    return "".join(map(str, d)) + str((11 - p) % 10)


def es_nif(r):
    n = r.randint(0, 99999999)
    return f"{n:08d}" + "TRWAGMYFPDXBNJZSQVHLCKE"[n % 23]


def pool(fn, k, r):
    vals = list(dict.fromkeys(fn() for _ in range(k * 3)))[:k]
    w = [1 / (i + 1) for i in range(len(vals))]  # Zipf-like, a few big towns
    return lambda: r.choices(vals, w)[0]


class Locale:
    """One locale's Faker, its random stream and its town, job and employer pools."""

    def __init__(self, loc: str, seed: int):
        self.loc, self.f, self.r = loc, stable_faker(loc), random.Random(f"{seed}-{loc}")
        self.f.seed_instance(seed)
        self.city, self.job, self.emp = pool(self.f.city, 30, self.r), pool(self.f.job, 40, self.r), \
            pool(self.f.company, 50, self.r)
        self.postcodes = {}

    def name(self, i):
        f = self.f
        return (f.first_name_female(), f.last_name()) if i % 2 == 0 else (f.first_name_male(), f.last_name())

    def ids(self):
        f, r = self.f, self.r
        if self.loc == "de_DE":
            return de_idnr(r), f.iban()
        if self.loc == "es_ES":
            return es_nif(r), f.iban()
        if self.loc == "sv_SE":
            return f.ssn(), iban("SE", "".join(r.choice(string.digits) for _ in range(20)))
        return f.ssn(), f.iban()


def record(base: Locale, i: int, who: Locale) -> dict:
    """One row. Name, town and occupation come from `who` (another locale in mixed_EU), the rest from `base`."""
    f, r = base.f, base.r
    fn, ln = who.name(i)
    c = who.city()
    pc = base.postcodes.setdefault(c, f.postcode())
    street = f.street_address()
    nid, ib = base.ids()
    ts = f.date_time_between(start_date=datetime(2023, 1, 1), end_date=datetime(2025, 6, 30))
    born = f.date_between(start_date=datetime(1935, 1, 1), end_date=datetime(2006, 12, 31))
    return {
        "customer_id": f"C{100000 + i}",
        "full_name": f"{fn} {ln}", "first_name": fn, "last_name": ln,
        "email": f"{fn}.{ln}@{f.free_email_domain()}".lower().replace(" ", ""),
        "phone": f.phone_number(), "national_id": nid, "iban": ib,
        "street_address": street, "full_address": f"{street}, {pc} {c}",
        "licence_plate": f.license_plate(), "postcode": pc, "city": c,
        "birth_date": born.strftime(DATEFMT[base.loc]),
        "sex": SEX[who.loc][i % 2], "occupation": who.job(), "employer": base.emp(),
        "signup_ts": ts.strftime("%Y-%m-%d %H:%M:%S"), "last_login_ip": f.ipv4_public(),
        "support_note": f"{f.sentence(nb_words=8)} {fn} {ln} {f.sentence(nb_words=6)}",
        "plan": r.choice(PLANS), "items_in_cart": str(r.randint(0, 12)),
    }


def write(out: Path, name: str, recs: list[dict], catalog: list[dict]) -> None:
    d = out / name
    d.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(recs).to_csv(d / "customers.csv", index=False)
    catalog += [{"dataset": name, "table": "customers", "column": c, "privacy_role": ro, "subtype": st}
                for c, ro, st in LABELS]


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--split", required=True, choices=["dev", "locked"])
    ap.add_argument("--rows", type=int, default=2000)
    a = ap.parse_args(argv)
    seed = SEEDS[a.split]
    locales = DEV if a.split == "dev" else LOCKED
    catalog = []
    for loc in locales:
        L = Locale(loc, seed)
        write(a.out, loc, [record(L, i, L) for i in range(a.rows)], catalog)
    if a.split == "dev":
        base = Locale("de_DE", seed + 1)
        mix = [Locale(loc, seed + 1) for loc in DEV]
        write(a.out, "mixed_EU", [record(base, i, base.r.choice(mix)) for i in range(a.rows)], catalog)
    pd.DataFrame(catalog).to_csv(a.out / "catalog.csv", index=False)
    print(f"wrote {len(catalog) // len(LABELS)} tables -> {a.out}")


if __name__ == "__main__":
    main()
