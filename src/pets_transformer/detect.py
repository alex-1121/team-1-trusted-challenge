"""Detect: label every column of a dataset with privacy_role and subtype from its values alone.

usage: python -m pets_transformer.detect --data <dataset folder> --dataset <name> --out <labels.csv> [--columns-only]

Column names are never read. Rules use value patterns, value statistics, small lexicons built from the
tuning datasets (lexicons/build.py), and table context (record keys, foreign keys, whether a table holds people).
Output format is the `pets-eval detect --pred` input; --columns-only writes `column,privacy_role,subtype`.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

MAX_ROWS = 5000
T = 0.6  # share of values a pattern must match
LEX_DIR = Path(__file__).parent / "lexicons"


def _lexicon(name: str) -> frozenset:
    lines = (LEX_DIR / name).read_text(encoding="utf-8").splitlines()
    return frozenset(x for x in lines[1:] if x)


NAMES = _lexicon("first_names.txt") | _lexicon("last_names.txt")
MUNICIPALITIES = _lexicon("municipalities.txt")
OCCUPATION = _lexicon("occupation_words.txt")
LANGUAGES = _lexicon("languages.txt")

RX = {k: re.compile(v) for k, v in {
    "hetu": r"\d{6}[-+A-FU-Y]\d{3}[0-9A-Y]",
    "iban": r"[A-Z]{2}\d{2}(?: ?[0-9A-Z]{2,4}){3,8}",
    "email": r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+",
    "url": r"https?://\S+",
    "masked_card": r"\d{4,6}[*xX]{4,8}\d{4}",
    "phone": r"(?:\+358|00358|0)\d{6,11}",
    "plate": r"[A-ZÅÄÖ]{2,3}-\d{1,3}",
    "mac": r"[0-9A-Fa-f]{2}(?:[:-][0-9A-Fa-f]{2}){5}",
    "ip": r"\d{1,3}(?:\.\d{1,3}){3}",
    "cidr": r"\d{1,3}(?:\.\d{1,3}){3}/\d{1,2}",
    "uuid": r"<?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4,12}.*",
    "hexhash": r"[0-9a-fA-F]{32,128}",
    "user_agent": r"[A-Za-z][\w.-]*/\d[\w.]*.*\(.*",
    "oid": r"\d+(?:\.\d+){3,}",
    "meter": r"\d{18}",
    "timestamp": r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?Z?",
    "date": r"\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[./]\d{1,2}[./]\d{2,4}|\d{2}/\d{2}",
    "hostname": r"[A-Z]{2,}(?:-[A-Z0-9]+){2,}|[A-Z]{3,}\d{2}",
    "employee_id": r"[A-Z]{2,4}-\d{4,6}",
    "address": r"[A-ZÅÄÖ][a-zåäöéü-]+(?: [A-ZÅÄÖ]?[a-zåäöéü-]+)? \d+[a-z]?(?: ?[A-Z] ?\d*)?(?:,.*)?",
    "income_band": r"[<>]?\d+(?:-\d+)?k\+?",
    "icd10": r"[A-TV-Z]\d{2}(?:\.?\d{1,2})?",
    "country": r"[A-Z]{2}",
    "id": r"[A-Z]{1,5}[-_]?\d{3,}[A-Z]?|[A-Z]{1,4}\d{2,}[A-Z]?|[A-Z]+\d+-\d+[A-Z]?",
    "filename": r"[\w.-]+\.[A-Za-z0-9]{2,4}",
    "postcode": r"\d{5}",
}.items()}
ORG = re.compile(r"\b(?:oy|oyj|ab|tmi|ky|ry|ltd|inc|gmbh|school|college|centre|center|hospital|clinic|isp|"
                 r"ravintola|kiinteistöt|säätiö|yhdistys)\b", re.I)
SEX = {"f", "m", "x", "n", "female", "male", "other", "nainen", "mies", "unknown", "u", "t"}


def _rate(v: pd.Series, key: str) -> float:
    return float(v.str.fullmatch(RX[key]).mean())


def _luhn(d: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(d)):
        n = int(ch)
        if i % 2:
            n = n * 2 - 9 if n > 4 else n * 2
        total += n
    return total % 10 == 0


def _numbers(v: pd.Series) -> pd.Series:
    s = v.str.replace(r"[\s ]", "", regex=True).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def _years(v: pd.Series) -> pd.Series:
    y = v.str.extract(r"^(\d{4})-|[./](\d{2,4})$")
    y = pd.to_numeric(y[0].fillna(y[1]), errors="coerce").dropna()
    return y.where(y >= 100, y.where(y > 30, y + 2000).where(y <= 30, y + 1900))


def _is_name(value: str) -> bool:
    toks = value.replace(",", " ").split()
    if not 1 <= len(toks) <= 4 or not all(t[:1].isupper() for t in toks) or ORG.search(value):
        return False
    return sum(t.lower() in NAMES for t in toks) * 2 >= len(toks)


def classify(s: pd.Series) -> tuple[str, str, str]:
    """Return (role, subtype, kind) for one column; kind 'key' or 'fk' marks id columns resolved per table."""
    v = s.dropna().astype(str).str.strip()
    v = v[v != ""]
    n = len(v)
    if n == 0:
        return "non_sensitive", "CATEGORY", ""
    nuniq = v.nunique()
    ratio = nuniq / n
    blanks = len(s) - n
    low = v.str.lower()
    compact = v.str.replace(r"[\s\-()]", "", regex=True)

    if _rate(v, "hetu") >= T:
        return "direct_identifier", "NATIONAL_ID", ""
    if _rate(v, "iban") >= T and compact.str.len().between(15, 34).mean() >= T:
        return "direct_identifier", "IBAN", ""
    if _rate(v, "email") >= T:
        top_domain = v.str.split("@").str[-1].str.lower().value_counts(normalize=True).iloc[0]
        return "direct_identifier", "USERNAME" if top_domain >= 0.9 and ratio < 0.9 else "EMAIL", ""
    if _rate(v, "url") >= T:
        return "free_text", "URL", ""
    digits = compact.str.fullmatch(r"\d{13,19}")
    if digits.mean() >= T:
        luhn = compact[digits].map(_luhn).mean()
        if luhn >= 0.9 and compact[digits].str[0].isin(list("23456")).mean() >= 0.9:
            if compact[digits].str.len().eq(15).mean() >= T:
                return "technical_identifier", "IMEI", ""
            return "direct_identifier", "PAYMENT_CARD", ""
    if _rate(v, "masked_card") >= T:
        return "direct_identifier", "PAYMENT_CARD", ""
    if float(compact.str.fullmatch(RX["phone"]).mean()) >= T:
        return "direct_identifier", "PHONE", ""
    if _rate(v, "plate") >= T:
        return "direct_identifier", "LICENSE_PLATE", ""
    if _rate(v, "mac") >= T:
        return "technical_identifier", "MAC_ADDRESS", ""
    if _rate(v, "ip") >= T:
        return "technical_identifier", "IP_ADDRESS", ""
    if _rate(v, "cidr") >= T:
        return "non_sensitive", "IP_ADDRESS", ""
    if _rate(v, "uuid") >= T:
        return "technical_identifier", "RECORD_ID", ""
    if _rate(v, "hexhash") >= T:
        return "non_sensitive", "OTHER", ""
    if _rate(v, "user_agent") >= T:
        return "technical_identifier", "USER_AGENT", ""
    if _rate(v, "oid") >= T:
        return "direct_identifier", "STUDENT_ID", ""
    if _rate(v, "meter") >= T:
        return "technical_identifier", "METER_ID", ""
    if _rate(v, "timestamp") >= T:
        return "quasi_identifier", "TIMESTAMP", ""
    if _rate(v, "date") >= T:
        y = _years(v)
        birth = len(y) and (y.median() <= 2010 or y.max() - y.min() >= 30)
        return "quasi_identifier", "BIRTH_DATE" if birth else "DATE", ""
    if _rate(v, "hostname") >= T:
        return "technical_identifier", "HOSTNAME", ""
    if _rate(v, "employee_id") >= T and ratio >= 0.9:
        return "direct_identifier", "EMPLOYEE_ID", ""
    if _rate(v, "address") >= T and ratio >= 0.5:
        return "direct_identifier", "STREET_ADDRESS", ""
    if low.isin(MUNICIPALITIES).mean() >= 0.7:
        return "quasi_identifier", "MUNICIPALITY", ""
    if v.map(_is_name).mean() >= 0.5:
        return "direct_identifier", "PERSON_NAME", ""
    if low.isin(MUNICIPALITIES).mean() >= 0.3:
        return "quasi_identifier", "LOCATION_NAME", ""
    if nuniq >= 2 and low.isin(LANGUAGES).mean() >= 0.9 and v.str.islower().mean() >= 0.9:
        return "quasi_identifier", "LANGUAGE", ""
    if 2 <= nuniq <= 4 and set(low.unique()) <= SEX:
        return "quasi_identifier", "SEX", ""
    if nuniq >= 2 and _rate(v, "country") >= T:
        return "quasi_identifier", "LOCATION_NAME", ""
    if nuniq == 2 and set(low.unique()) == {"true", "false"}:
        return "sensitive_attribute", "OTHER", ""
    if _rate(v, "income_band") >= T:
        return "sensitive_attribute", "FINANCIAL_DATA", ""
    if nuniq >= 15 and _rate(v, "icd10") >= T and v.str[0].nunique() >= 3:
        return "sensitive_attribute", "DIAGNOSIS_CODE", ""

    num = _numbers(v)
    if num.notna().mean() >= 0.95:
        return _classify_numeric(v, num.dropna(), ratio, nuniq, blanks)

    if v.str.contains("\\", regex=False).mean() >= T:
        return "free_text", "FREE_TEXT", ""
    if _rate(v, "id") >= T:
        return ("record_key" if ratio >= 0.99 and not blanks else "technical_identifier"), "RECORD_ID", (
            "key" if ratio >= 0.99 and not blanks else "fk")
    if v.str.contains(ORG).mean() >= 0.3:
        return "quasi_identifier", "ORG_NAME", ""
    tokens = v.str.split().str.len()
    if nuniq >= 20 and (tokens.mean() >= 4 or (tokens.mean() >= 2.5 and v.str.len().mean() >= 15 and nuniq >= 50)):
        return "free_text", "FREE_TEXT", ""
    if nuniq >= 20 and _rate(v, "filename") >= T and ratio >= 0.5:
        return "free_text", "FREE_TEXT", ""
    if nuniq >= 3 and low.map(lambda x: any(w in OCCUPATION for w in re.findall(r"[^\W\d_]+", x))).mean() >= T:
        return "quasi_identifier", "OCCUPATION", ""
    return "non_sensitive", "CATEGORY", ""


def _classify_numeric(v: pd.Series, num: pd.Series, ratio: float, nuniq: int, blanks: int) -> tuple[str, str, str]:
    decimals = v.str.extract(r"[.,](\d+)$")[0].str.len().fillna(0)
    q05, q95 = num.quantile(0.05), num.quantile(0.95)
    if decimals.ge(3).mean() >= T and min(abs(q05), abs(q95)) >= 1 and num.abs().max() <= 180 and q95 - q05 < 6:
        return "quasi_identifier", "GPS_COORDINATE", ""
    if nuniq >= 5 and v.str.fullmatch(RX["postcode"]).all():
        return "quasi_identifier", "POSTCODE", ""
    integer = (num == num.round()).all() and decimals.eq(0).all()
    if integer:
        if v.str.fullmatch(r"\d{6,}").mean() >= T and ratio >= 0.5:
            if ratio >= 0.99 and not blanks:
                return "record_key", "RECORD_ID", "key"
            return "technical_identifier", "ACCOUNT_ID", "fk" if ratio < 0.99 else ""
        if num.min() >= 0 and num.max() <= 110 and nuniq >= 30 and 15 <= num.mean() <= 70:
            return "quasi_identifier", "AGE", ""
        if num.min() >= 0 and num.max() <= 300 and 5 <= nuniq <= 300:
            return "sensitive_attribute", "OTHER", ""
        return "non_sensitive", "MEASUREMENT", ""
    if decimals.le(2).all() and decimals.eq(2).mean() >= 0.5 and ratio >= 0.3:
        return "quasi_identifier", "FINANCIAL_DATA", ""
    return "non_sensitive", "MEASUREMENT", ""


PERSON_SUBTYPES = {"BIRTH_DATE", "SEX", "AGE"}


def detect_dataset(data_dir: Path, dataset: str) -> pd.DataFrame:
    tables = {f.stem: pd.read_csv(f, dtype=str, nrows=MAX_ROWS) for f in sorted(Path(data_dir).glob("*.csv"))}
    rows = []
    for t, df in tables.items():
        for c in df.columns:
            role, sub, kind = classify(df[c])
            rows.append(dict(dataset=dataset, table=t, column=c, privacy_role=role, subtype=sub, kind=kind))
    lab = pd.DataFrame(rows, columns=["dataset", "table", "column", "privacy_role", "subtype", "kind"])
    if lab.empty:
        return lab.drop(columns="kind")

    # the first unique id column of a table is its record key; later unique id columns are technical ids
    keys = {}
    for t, g in lab[lab.kind == "key"].groupby("table", sort=False):
        first = g.index[0]
        keys[t] = set(tables[t][lab.at[first, "column"]].dropna().str.strip())
        lab.loc[g.index[1:], ["privacy_role", "kind"]] = ["technical_identifier", ""]

    def person(t: str) -> bool:
        g = lab[(lab.table == t) & (lab.kind != "fk")]
        return bool(g.privacy_role.isin(["direct_identifier", "technical_identifier"]).any()
                    or g.subtype.isin(PERSON_SUBTYPES).any())

    is_person = {t: person(t) for t in tables}
    for i in lab.index[lab.kind == "fk"]:
        t = lab.at[i, "table"]
        vals = tables[t][lab.at[i, "column"]].dropna().str.strip()
        target = next((k for k, ks in keys.items() if k != t and vals.isin(ks).mean() >= 0.8), None)
        if target is None:
            if vals.nunique() <= 30:
                lab.loc[i, ["privacy_role", "subtype"]] = ["non_sensitive", "CATEGORY"]
            else:
                is_person[t] = True
        elif is_person[target]:
            lab.loc[i, ["privacy_role", "subtype"]] = ["technical_identifier", "RECORD_ID"]
            is_person[t] = True
        else:
            gps = (lab.table == target) & (lab.subtype == "GPS_COORDINATE")
            lab.loc[i, ["privacy_role", "subtype"]] = ["quasi_identifier",
                                                       "LOCATION_NAME" if gps.any() else "CATEGORY"]
    # tables that hold no person (reference data, weather, aggregates) are safe to share as is
    ref = lab.table.map(lambda t: not is_person[t]) & lab.privacy_role.isin(["quasi_identifier",
                                                                              "sensitive_attribute"])
    lab.loc[ref, "privacy_role"] = "non_sensitive"
    return lab.drop(columns="kind")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", required=True, help="dataset folder holding the table CSVs")
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--columns-only", action="store_true", help="write column,privacy_role,subtype")
    a = ap.parse_args(argv)
    lab = detect_dataset(Path(a.data), a.dataset)
    if a.columns_only:
        lab = lab[["column", "privacy_role", "subtype"]]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    lab.to_csv(a.out, index=False)
    print(f"wrote {len(lab)} labels -> {a.out}")


if __name__ == "__main__":
    main()
