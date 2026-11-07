import hashlib
import hmac

import pandas as pd
from pets_eval import parse


def hmac_pseudonym(s: pd.Series, key: bytes) -> pd.Series:
    # The "P" prefix is required: a bare hex string starting 04... trips the pets-eval PHONE pattern, and "P-" would not help.
    return s.map(lambda x: "P" + hmac.new(key, str(x).encode(), hashlib.sha256).hexdigest()[:16])


def drop(df: pd.DataFrame, col: str) -> pd.DataFrame:
    return df.drop(columns=[col])


def hour_of_day(s: pd.Series) -> pd.Series:
    return parse.to_datetime(s).dt.strftime("%H:00")


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
