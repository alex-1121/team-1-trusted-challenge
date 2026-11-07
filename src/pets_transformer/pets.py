import hashlib
import hmac

import pandas as pd
from pets_eval import parse


def hmac_pseudonym(s: pd.Series, key: bytes) -> pd.Series:
    # The "P" prefix is required: a bare hex string starting 04... trips the pets-eval PHONE pattern, and "P-" would not help.
    return s.map(lambda x: "P" + hmac.new(key, str(x).encode(), hashlib.sha256).hexdigest()[:16], na_action="ignore")


def token(s: pd.Series, key: bytes, prefix: str = "T") -> pd.Series:
    """Keyed token for a record key or join key: the same key and value give the same token in every table,
    so joins survive, while the token carries no order (a sequential id would give back arrival order)."""
    return s.map(lambda x: prefix + hmac.new(key, b"token:" + str(x).encode(), hashlib.sha256).hexdigest()[:16], na_action="ignore")


def drop(df: pd.DataFrame, col: str) -> pd.DataFrame:
    return df.drop(columns=[col])


def hour_of_day(s: pd.Series, block: int = 1) -> pd.Series:
    h = parse.to_datetime(s).dt.hour
    return (h - h % block).map(lambda x: f"{int(x):02d}:00" if x == x else x)


def age_band(s: pd.Series, width: int = 10) -> pd.Series:
    return parse.to_age_band(parse.age_from_birth(s), width=width)


def top_n_exact_else_other(s: pd.Series, n: int, other: str = "other", ignore: tuple = ("non-resident",)) -> pd.Series:
    top = s[~s.isin(ignore)].value_counts().index[:n]
    return s.where(s.isin(top), other)


def copy_to(df: pd.DataFrame, src: str, dst: str) -> pd.DataFrame:
    df[dst] = df[src]
    return df


def withhold(columns) -> list:
    return list(columns)


def month(s: pd.Series) -> pd.Series:
    """Calendar month only, YYYY-MM."""
    return parse.to_datetime(s).dt.strftime("%Y-%m").where(lambda x: x.notna(), s.where(s.isna()))


def week(s: pd.Series) -> pd.Series:
    """ISO week only, YYYY-Www."""
    d = parse.to_datetime(s)
    iso = d.dt.isocalendar()
    return (iso.year.astype("Int64").astype(str) + "-W" + iso.week.astype("Int64").astype(str).str.zfill(2)).where(d.notna())


def day(s: pd.Series) -> pd.Series:
    """Date only, YYYY-MM-DD (time of day dropped)."""
    return parse.to_datetime(s).dt.strftime("%Y-%m-%d").where(lambda x: x.notna())


def round_decimals(s: pd.Series, decimals: int) -> pd.Series:
    """Coordinates snapped to a grid: 2 decimals of latitude is about 1.1 km, 3 decimals about 110 m."""
    v = pd.to_numeric(s, errors="coerce")
    return v.round(decimals).map(lambda x: f"{x:.{decimals}f}" if x == x else x)


def prefix(s: pd.Series, n: int) -> pd.Series:
    """First n characters only (postcode area)."""
    return s.str[:n]
