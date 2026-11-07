"""Detect: label every column of a dataset with privacy_role and subtype from its values alone.

usage: python -m pets_transformer.detect --data <dataset folder> --dataset <name> --out <labels.csv> [--columns-only]

Column names are never read. Rules use value patterns, value statistics, small lexicons built from the
tuning datasets (lexicons/build.py), and table context (record keys, foreign keys, whether a table holds people).
Output format is the `pets-eval detect --pred` input; --columns-only writes `column,privacy_role,subtype`.
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .semantic import requested_mode, resolve
from .semantic.decide import combine, decide, treatment
from .semantic.types import PROTECT_RANK as _PROTECT, TYPE_LABEL
from .semantic.features import sample_values
from .semantic.model import load_model

MAX_ROWS = 5000
T = 0.6  # share of values a pattern must match
LEX_DIR = Path(__file__).parent / "lexicons"


def _lexicon(name: str) -> frozenset:
    lines = (LEX_DIR / name).read_text(encoding="utf-8").splitlines()
    return frozenset(x for x in lines[1:] if x)


NAMES = _lexicon("first_names.txt") | _lexicon("last_names.txt")
MUNICIPALITIES = _lexicon("municipalities.txt")
OCCUPATION = _lexicon("occupation_words.txt")
# Finnish titles are compounds (lähi+hoitaja), so a word also matches when it ends with one of these
OCCUPATION_FI = _lexicon("occupation_words_fi.txt")
LANGUAGES = _lexicon("languages.txt")

RX = {k: re.compile(v) for k, v in {
    "hetu": r"\d{6}[-+A-FU-Y]\d{3}[0-9A-Y]",
    "hetu_nosign": r"(?:0[1-9]|[12]\d|3[01])(?:0[1-9]|1[0-2])\d{5}[0-9A-Y]",
    "full_address": r"[A-ZÅÄÖ][a-zåäöéü-]+(?: [A-ZÅÄÖ]?[a-zåäöéü-]+)? \d+[a-z]?(?: ?[A-Z] ?\d*)?, \d{5} [^\W\d_][\w -]*",
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
    "record_id": r"([A-Za-z]{1,5})[-_]?(?:\d+[-_])?(\d{3,18})",  # 18 digits still fit an int64
}.items()}
ORG = re.compile(r"\b(?:oy|oyj|ab|tmi|ky|ry|ltd|inc|gmbh|school|college|centre|center|hospital|clinic|isp|"
                 r"ravintola|kiinteistöt|säätiö|yhdistys)\b", re.I)
HETU_CHECK = "0123456789ABCDEFHJKLMNPRSTUVWXY"
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


def _is_occupation(value: str) -> bool:
    return any(w in OCCUPATION or w.endswith(tuple(OCCUPATION_FI)) for w in re.findall(r"[^\W\d_]+", value))


def _record_id(v: pd.Series, blanks: int) -> bool:
    """Unique values, one fixed letter prefix, near-sequential trailing number (SR-2024-000001)."""
    m = v.str.extract("^" + RX["record_id"].pattern + "$").dropna()
    if blanks or len(m) < 0.99 * len(v) or m[0].nunique() != 1 or v.nunique() < len(v):
        return False
    num = m[1].astype(int)
    return num.nunique() == len(m) and len(m) / (num.max() - num.min() + 1) >= 0.5


def classify(s: pd.Series) -> tuple[str, str, str]:
    """Return (role, subtype, kind) for one column; kind 'key' or 'fk' marks id columns resolved per table."""
    return classify_traced(s)[:3]


def classify_traced(s: pd.Series) -> tuple[str, str, str, str]:
    """classify plus the rule that fired: "pre" (pattern rules before the word lists), "lex_*" (a word list, see
    semantic.types.LEXICON_RULES), "numeric", "fallthrough" (nothing matched: CATEGORY) or "rule" (any other)."""
    v = s.dropna().astype(str).str.strip()
    v = v[v != ""]
    n = len(v)
    if n == 0:
        return "non_sensitive", "CATEGORY", "", "pre"
    nuniq = v.nunique()
    ratio = nuniq / n
    blanks = len(s) - n
    low = v.str.lower()
    compact = v.str.replace(r"[\s\-()]", "", regex=True)

    # a HETU may arrive without its century sign; there the checksum keeps plain 10-digit codes out
    hv = v.str.replace(r"^[^\W\d_]+:?\s+", "", regex=True)  # a label word may precede the code ("HETU 210390-945N")
    nosign = hv.str.fullmatch(RX["hetu_nosign"])
    nosign[nosign] = hv[nosign].map(lambda x: HETU_CHECK[int(x[:9]) % 31] == x[9])
    if (hv.str.fullmatch(RX["hetu"]) | nosign).mean() >= T:
        return "direct_identifier", "NATIONAL_ID", "", "pre"
    if _rate(v, "iban") >= T and compact.str.len().between(15, 34).mean() >= T:
        return "direct_identifier", "IBAN", "", "pre"
    if _rate(v, "email") >= T:
        top_domain = v.str.split("@").str[-1].str.lower().value_counts(normalize=True).iloc[0]
        return "direct_identifier", "USERNAME" if top_domain >= 0.9 and ratio < 0.9 else "EMAIL", "", "pre"
    if _rate(v, "url") >= T:
        return "free_text", "URL", "", "pre"
    digits = compact.str.fullmatch(r"\d{13,19}")
    if digits.mean() >= T:
        luhn = compact[digits].map(_luhn).mean()
        if luhn >= 0.9 and compact[digits].str[0].isin(list("23456")).mean() >= 0.9:
            if compact[digits].str.len().eq(15).mean() >= T:
                return "technical_identifier", "IMEI", "", "pre"
            return "direct_identifier", "PAYMENT_CARD", "", "pre"
    if _rate(v, "masked_card") >= T:
        return "direct_identifier", "PAYMENT_CARD", "", "pre"
    if float((compact.str.fullmatch(RX["phone"]) & ~v.str.fullmatch(r"0\d{7}")).mean()) >= T:
        return "direct_identifier", "PHONE", "", "pre"
    if _rate(v, "plate") >= T:
        return "direct_identifier", "LICENSE_PLATE", "", "pre"
    if _rate(v, "mac") >= T:
        return "technical_identifier", "MAC_ADDRESS", "", "pre"
    if _rate(v, "ip") >= T:
        return "technical_identifier", "IP_ADDRESS", "", "pre"
    if _rate(v, "cidr") >= T:
        return "non_sensitive", "IP_ADDRESS", "", "pre"
    if _rate(v, "uuid") >= T:
        return "technical_identifier", "RECORD_ID", "", "pre"
    if _rate(v, "hexhash") >= T:
        return "non_sensitive", "OTHER", "hash", "pre"
    if _rate(v, "user_agent") >= T:
        return "technical_identifier", "USER_AGENT", "", "pre"
    if _rate(v, "oid") >= T:
        return "direct_identifier", "STUDENT_ID", "", "pre"
    if _rate(v, "meter") >= T:
        return "technical_identifier", "METER_ID", "", "pre"
    if _rate(v, "timestamp") >= T:
        return "quasi_identifier", "TIMESTAMP", "", "pre"
    if _rate(v, "date") >= T:
        y = _years(v)
        birth = len(y) and (y.median() <= 2010 or y.max() - y.min() >= 30)
        return "quasi_identifier", "BIRTH_DATE" if birth else "DATE", "", "pre"
    if _record_id(v, blanks):
        return "record_key", "RECORD_ID", "seqkey", "pre"
    if _rate(v, "hostname") >= T:
        return "technical_identifier", "HOSTNAME", "", "pre"
    if _rate(v, "employee_id") >= T and ratio >= 0.9:
        return "direct_identifier", "EMPLOYEE_ID", "", "pre"
    if _rate(v, "full_address") >= T:
        return "direct_identifier", "STREET_ADDRESS", "", "pre"
    if _rate(v, "address") >= T and ratio >= 0.5:
        return "direct_identifier", "STREET_ADDRESS", "", "pre"
    if low.isin(MUNICIPALITIES).mean() >= 0.7:
        return "quasi_identifier", "MUNICIPALITY", "", "lex_municipality"
    if v.map(_is_name).mean() >= 0.5:
        return "direct_identifier", "PERSON_NAME", "", "lex_name"
    if low.isin(MUNICIPALITIES).mean() >= 0.3:
        return "quasi_identifier", "LOCATION_NAME", "", "lex_place"
    if nuniq >= 2 and low.isin(LANGUAGES).mean() >= 0.9 and v.str.islower().mean() >= 0.9:
        return "quasi_identifier", "LANGUAGE", "", "lex_language"
    if 2 <= nuniq <= 4 and set(low.unique()) <= SEX:
        return "quasi_identifier", "SEX", "", "lex_sex"
    if nuniq >= 2 and _rate(v, "country") >= T:
        return "quasi_identifier", "LOCATION_NAME", "", "rule"
    if nuniq == 2 and set(low.unique()) == {"true", "false"}:
        return "sensitive_attribute", "OTHER", "", "rule"
    if _rate(v, "income_band") >= T:
        return "sensitive_attribute", "FINANCIAL_DATA", "", "rule"
    if nuniq >= 15 and _rate(v, "icd10") >= T and v.str[0].nunique() >= 3:
        return "sensitive_attribute", "DIAGNOSIS_CODE", "", "rule"

    num = _numbers(v)
    if num.notna().mean() >= 0.95:
        return (*_classify_numeric(v, num.dropna(), ratio, nuniq, blanks), "numeric")

    if v.str.contains("\\", regex=False).mean() >= T:
        return "free_text", "FREE_TEXT", "", "rule"
    if _rate(v, "id") >= T:
        return ("record_key" if ratio >= 0.99 and not blanks else "technical_identifier"), "RECORD_ID", (
            "key" if ratio >= 0.99 and not blanks else "fk"), "rule"
    if v.str.contains(ORG).mean() >= 0.3:
        return "quasi_identifier", "ORG_NAME", "", "lex_org"
    tokens = v.str.split().str.len()
    if nuniq >= 20 and (tokens.mean() >= 4 or (tokens.mean() >= 2.5 and v.str.len().mean() >= 15 and nuniq >= 50)):
        return "free_text", "FREE_TEXT", "", "rule"
    if nuniq >= 20 and _rate(v, "filename") >= T and ratio >= 0.5:
        return "free_text", "FREE_TEXT", "", "rule"
    if nuniq >= 3 and low.map(_is_occupation).mean() >= T:
        return "quasi_identifier", "OCCUPATION", "", "lex_occupation"
    return "non_sensitive", "CATEGORY", "", "fallthrough"


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
        if 1000 <= q05 and q95 <= 15000 and q95 <= 5 * q05:
            return "sensitive_attribute", "FINANCIAL_DATA", ""  # monthly pay: cents, narrow band of a few thousand
        return "quasi_identifier", "FINANCIAL_DATA", ""
    return "non_sensitive", "MEASUREMENT", ""


PERSON_SUBTYPES = {"BIRTH_DATE", "SEX", "AGE"}


def _one_to_one(a: pd.Series, b: pd.Series) -> bool:
    pairs = pd.DataFrame({"a": a.str.strip(), "b": b.str.strip()}).dropna().drop_duplicates()
    return len(pairs) >= 20 and len(pairs) == pairs.a.nunique() == pairs.b.nunique()


def _union_pairs(df: pd.DataFrame, lab: pd.DataFrame, t: str) -> None:
    """A code column blank on part of the rows, next to an amount that is zero exactly there (union and union fee)."""
    rows = lab.index[lab.table == t]
    codes = [i for i in rows if lab.at[i, "subtype"] == "CATEGORY"]
    for i in codes:
        code = df[lab.at[i, "column"]].str.strip()
        code = code.mask(code == "")
        blank = code.isna()
        if not 0.05 <= blank.mean() <= 0.95 or not 2 <= code.nunique() <= 30:
            continue
        for j in rows:
            v = df[lab.at[j, "column"]].dropna().astype(str).str.strip()
            if j == i or not len(v) or v.str.fullmatch(r"-?\d[\d\s ]*[.,]\d{2}").mean() < 0.9:
                continue
            zero = _numbers(df[lab.at[j, "column"]].fillna("").astype(str)).eq(0)
            if (zero == blank).mean() >= 0.95 and zero[blank].mean() >= 0.95:
                lab.loc[i, ["privacy_role", "subtype"]] = ["sensitive_attribute", "CATEGORY"]
                lab.loc[j, ["privacy_role", "subtype"]] = ["sensitive_attribute", "FINANCIAL_DATA"]


ESCALATE = ("direct_identifier", "quasi_identifier", "sensitive_attribute")


def _wide_sample(f: Path, n: int = MAX_ROWS) -> pd.DataFrame | None:
    """n rows drawn at random over the whole file (fixed seed), or None when the file has no more than n rows."""
    df = pd.read_csv(f, dtype=str)
    return df.sample(n, random_state=0).sort_index() if len(df) > n else None


PROBS_COLUMNS = ["dataset", "table", "column", "rule", "privacy_role", "subtype", "top1", "p1", "top2", "p2", "top3",
                 "p3", "decision", "flag"]
REVIEW_COLUMNS = PROBS_COLUMNS + ["reason"]


@dataclass
class DetectReport:
    """Labels plus what the model said. type_probs and needs_review hold names, types and probabilities only."""
    labels: pd.DataFrame
    type_probs: pd.DataFrame
    needs_review: pd.DataFrame
    mode: str


def _label_column(s: pd.Series, wide: pd.Series | None, model,
                  apply: bool = True) -> tuple[tuple[str, str, str], dict | None]:
    """Word lists first, on the first MAX_ROWS rows (s). A column they judge non-sensitive there gets a second word-list
    look on rows from the whole file (wide), and can only move to a more protective label. Then, with a model, a
    column the pattern and number rules did not settle is read once by the model (on the wide rows when the second
    look ran, so a flag only the whole file shows is not lost), and combine decides. Returns the (role, subtype, kind)
    label and its type_probs row or None.

    apply=False (advisor mode): the word-list label stands whatever the model says. A model label that would change
    the column's treatment is flagged "suggest" (unless combine already flagged it) and named in the reason."""
    role, sub, kind, rule = classify_traced(s)
    read = (role, sub, rule)  # the word-list reading of the rows the model reads
    if role == "non_sensitive" and wide is not None:
        second = classify_traced(wide)
        if second[0] in ESCALATE:
            role, sub, kind, rule = second
        read, s = (second[0], second[1], second[3]), wide
    if model is None or read[2] in ("pre", "numeric"):
        return (role, sub, kind), None
    probs = model.predict_proba(sample_values(s))
    if probs is None:
        return (role, sub, kind), None
    dec = decide(probs)
    r2, s2, flag = combine(*read, dec)
    reason = dec.reason
    if not apply:
        if treatment(r2, s2) != treatment(role, sub):
            flag = flag or "suggest"
            reason += f"; model suggests {r2} {s2}"
        r2, s2 = role, sub
    if (r2, s2) != (role, sub):
        kind = ""
    top = sorted(probs, key=probs.get, reverse=True)[:3]
    # the role the model would give: used to drop flags that a table rule makes moot (see _drop_moot_flags)
    model_role = max((TYPE_LABEL[dec.type][0], TYPE_LABEL[top[0]][0]), key=lambda r: _PROTECT[r])
    row = dict(rule=read[2], decision=dec.decision, flag=flag or "", reason=reason, model_role=model_role, word_role=role)
    for i, t in enumerate(top, 1):
        row[f"top{i}"], row[f"p{i}"] = t, round(probs[t], 3)
    return (r2, s2, kind), row


def detect_dataset(data_dir: Path, dataset: str, semantic: str | None = None) -> pd.DataFrame:
    """Labels only. Advisor mode never changes a label, so only an explicit hybrid request (argument or
    PETS_SEMANTIC) loads the model here; select and protect without --labels stay as fast as the word lists."""
    if requested_mode(semantic) != "hybrid":
        semantic = "lexicon"
    return detect_dataset_report(data_dir, dataset, semantic).labels


def detect_dataset_report(data_dir: Path, dataset: str, semantic: str | None = None) -> DetectReport:
    """semantic: "lexicon" (word lists only), "advisor" (word-list labels, the model only flags columns for review),
    "hybrid" (word lists, then the model labels the rest) or None (env PETS_SEMANTIC, else advisor when the model
    loads). Without a model the default runs lexicon (load_model warns once); a mode asked for by name raises
    semantic.ModelUnavailable."""
    mode, model = resolve(semantic, load_model)
    apply = mode == "hybrid"
    tables = {f.stem: pd.read_csv(f, dtype=str, nrows=MAX_ROWS) for f in sorted(Path(data_dir).glob("*.csv"))}
    # The rules read the first MAX_ROWS rows (keys and order rules are tuned on file order). The first rows of a
    # time-sorted table are its first weeks, so a column judged non-sensitive there gets a second look on rows from
    # the whole file (_label_column), and can only move to a more protective label, never to a less protective one.
    wide = {f.stem: _wide_sample(f) for f in sorted(Path(data_dir).glob("*.csv"))}
    rows, prob_rows = [], []
    for t, df in tables.items():
        for c in df.columns:
            (role, sub, kind), prow = _label_column(df[c], None if wide[t] is None else wide[t][c], model, apply)
            rows.append(dict(dataset=dataset, table=t, column=c, privacy_role=role, subtype=sub, kind=kind))
            if prow is not None:
                prob_rows.append(dict(dataset=dataset, table=t, column=c, **prow))
    lab = pd.DataFrame(rows, columns=["dataset", "table", "column", "privacy_role", "subtype", "kind"])
    if lab.empty:
        return _report(lab.drop(columns="kind"), prob_rows, mode)

    # a table's record key is its first sequential prefixed id, else its first unique id; other unique ids are technical
    keys = {}
    for t, g in lab[lab.kind.isin(["key", "seqkey"])].groupby("table", sort=False):
        first = (g.index[g.kind == "seqkey"].tolist() or g.index.tolist())[0]
        keys[t] = set(tables[t][lab.at[first, "column"]].dropna().str.strip())
        lab.loc[g.index.drop(first), ["privacy_role", "kind"]] = ["technical_identifier", ""]
        lab.loc[first, "kind"] = "key"

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
                # a short-prefix number (KC-4450) that points at no table and repeats over rows numbers a person
                if (vals.str.fullmatch(RX["employee_id"]).mean() >= T and vals.nunique() >= 100
                        and vals.nunique() <= 0.5 * len(vals)):
                    lab.loc[i, ["privacy_role", "subtype"]] = ["direct_identifier", "EMPLOYEE_ID"]
        elif is_person[target]:
            lab.loc[i, ["privacy_role", "subtype"]] = ["technical_identifier", "RECORD_ID"]
            is_person[t] = True
        else:
            gps = (lab.table == target) & (lab.subtype == "GPS_COORDINATE")
            lab.loc[i, ["privacy_role", "subtype"]] = ["quasi_identifier",
                                                       "LOCATION_NAME" if gps.any() else "CATEGORY"]
    for t, df in tables.items():
        ids = lab.index[(lab.table == t) & lab.privacy_role.isin(["direct_identifier", "technical_identifier"])]
        for i in lab.index[(lab.table == t) & (lab.kind == "hash")]:
            if any(_one_to_one(df[lab.at[i, "column"]], df[lab.at[j, "column"]]) for j in ids):
                lab.loc[i, "privacy_role"] = "technical_identifier"  # a hash of a per-person id is a pseudonym
        _union_pairs(df, lab, t)
    # tables that hold no person (reference data, weather, aggregates) are safe to share as is
    ref = lab.table.map(lambda t: not is_person[t]) & lab.privacy_role.isin(["quasi_identifier",
                                                                              "sensitive_attribute"])
    lab.loc[ref, "privacy_role"] = "non_sensitive"
    _drop_moot_flags(prob_rows, is_person)
    return _report(lab.drop(columns="kind"), prob_rows, mode)


DEMOTED = ("quasi_identifier", "sensitive_attribute", "non_sensitive")


def _drop_moot_flags(prob_rows: list[dict], is_person: dict) -> None:
    """A table that holds no person is shared as is: its quasi-identifier and sensitive columns become non-sensitive.
    A flag there is moot when both the word lists' role and the model's role end as non-sensitive, so it is dropped
    (the row stays in type_probs, its reason says why). A flag where either side says direct identifier, free text
    or key is kept: that reading would make the table a person table."""
    for r in prob_rows:
        if r["flag"] and not is_person[r["table"]] and r["word_role"] in DEMOTED and r["model_role"] in DEMOTED:
            r["reason"] += f"; flag {r['flag']} dropped: table holds no person, both readings end non-sensitive"
            r["flag"] = ""


def _report(lab: pd.DataFrame, prob_rows: list[dict], mode: str) -> DetectReport:
    """type_probs carries each model-read column's final label (after the table rules)."""
    probs = pd.DataFrame(prob_rows, columns=REVIEW_COLUMNS)
    if len(probs):
        final = lab.set_index(["table", "column"])[["privacy_role", "subtype"]]
        probs[["privacy_role", "subtype"]] = final.loc[list(zip(probs.table, probs.column))].to_numpy()
    review = probs[probs.flag != ""].reset_index(drop=True)
    return DetectReport(lab, probs[PROBS_COLUMNS], review, mode)


def review_warning(review: pd.DataFrame, with_dataset: bool = False) -> str:
    """One line naming every flagged column (table.column, or dataset/table.column), or "" when nothing is flagged."""
    if review.empty:
        return ""
    where = [f"{d}/{t}" if with_dataset else t for d, t in zip(review.dataset, review.table)]
    cols = ", ".join(f"{w}.{c} ({f})" for w, c, f in zip(where, review.column, review.flag))
    return f"WARNING: {len(review)} column(s) need review: {cols}"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", required=True, help="dataset folder holding the table CSVs")
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--columns-only", action="store_true", help="write column,privacy_role,subtype")
    ap.add_argument("--semantic", choices=["lexicon", "advisor", "hybrid"], default=None,
                    help="word lists only (lexicon); word-list labels with the model flagging columns for review "
                         "(advisor); or the model also labels what the word lists cannot place (hybrid). Default: env "
                         "PETS_SEMANTIC, else advisor when the model is installed")
    ap.add_argument("--review-dir", default="results",
                    help="folder for <out stem>_type_probs.csv and _needs_review.csv, written only when the model "
                         "ran (default: results/, kept apart from the labels so they never land in pets_submission/)")
    a = ap.parse_args(argv)
    report = detect_dataset_report(Path(a.data), a.dataset, a.semantic)
    lab = report.labels
    if a.columns_only:
        lab = lab[["column", "privacy_role", "subtype"]]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    lab.to_csv(a.out, index=False)
    print(f"wrote {len(lab)} labels -> {a.out} (mode {report.mode})")
    if report.mode != "lexicon":
        stem, review_dir = Path(a.out).stem, Path(a.review_dir)
        review_dir.mkdir(parents=True, exist_ok=True)
        report.type_probs.to_csv(review_dir / f"{stem}_type_probs.csv", index=False)
        report.needs_review.to_csv(review_dir / f"{stem}_needs_review.csv", index=False)
    if line := review_warning(report.needs_review):
        print(line)


if __name__ == "__main__":
    main()
