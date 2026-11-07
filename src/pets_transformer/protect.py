import json
import os
import secrets
from pathlib import Path

import pandas as pd

import numpy as np

from . import detect, pets, repair


def _plan_row(table, column, role, pet, params, reason, note=""):
    return {"table": table, "column": column, "role": role, "pet": pet, "params": params and str(params) or "", "reason": reason, "note": note}


# Roles a named rule is designed for; a pet not listed (drop, ...) is safe on any role and never notes.
EXPECTED_ROLES = {
    "pseudonym": {"direct_identifier"},
    "age_band": {"quasi_identifier"},
    "hour_of_day": {"quasi_identifier"},
    "top_n_exact_else_other": {"quasi_identifier"},
    "keep": {"technical_identifier", "record_key"},
    "token": {"technical_identifier", "record_key"},
    "month": {"quasi_identifier"}, "week": {"quasi_identifier"}, "day": {"quasi_identifier"}, "date_hour": {"quasi_identifier"}, "duration": {"quasi_identifier"},
    "round_decimals": {"quasi_identifier"}, "prefix": {"quasi_identifier"},
}


def resolve(name, col, role, contract):
    """Named column rule wins; else the role rule for the detected role; else error. Returns (rule, note)."""
    named = contract["columns"].get(name, {}).get(col)
    by_role = contract.get("roles", {}).get(name, {}).get(role)
    if named:
        expected = EXPECTED_ROLES.get(named["pet"])
        disagree = role and expected and role not in expected
        return named, f"named rule wins over detected role {role}" if disagree else ""
    if by_role:
        return by_role, ""
    raise ValueError(f"{name}.{col}: no column rule and no role rule for detected role {role!r}")


def column_values(s, rule, key):
    """One column rule applied to one column (any rule but drop)."""
    pet, params = rule["pet"], rule.get("params", {})
    if pet == "pseudonym":
        return pets.hmac_pseudonym(s, key)
    if pet == "token":
        return pets.token(s, key, params.get("prefix", "T"))
    if pet == "hour_of_day":
        return pets.hour_of_day(s, params.get("block", 1))
    if pet == "age_band":
        return pets.age_band(s, params.get("width", 10))
    if pet in ("month", "week", "day", "date_hour"):
        return getattr(pets, pet)(s)
    if pet == "round_decimals":
        return pets.round_decimals(s, params["decimals"])
    if pet == "prefix":
        return pets.prefix(s, params["n"])
    if pet == "top_n_exact_else_other":
        return pets.top_n_exact_else_other(s, params["n"])
    if pet == "keep":
        return s
    raise ValueError(f"unknown pet {pet!r}")


def protect_table(name, df, contract, key, roles=None):
    """roles maps column -> detected privacy_role for this table."""
    roles = roles or {}
    spec = contract["columns"].get(name, {})
    unknown = [c for c in spec if c not in df.columns]
    if unknown:
        raise ValueError(f"{name}: contract names columns not in table: {unknown}")
    out = df.copy()
    plan = []
    for col in df.columns:
        cs, note = resolve(name, col, roles.get(col, ""), contract)
        pet, params = cs["pet"], cs.get("params", {})
        if pet == "drop":
            out = pets.drop(out, col)
        elif pet == "duration":
            # the column becomes the time since another column of the same row, under its own name
            out = pets.drop(out, col)
            out[params["as"]] = pets.duration(df[params["since"]], df[col], params.get("unit", "hours"), params.get("decimals", 0)).values
        else:
            out[col] = column_values(df[col], cs, key)
        for dst in params.get("also_as", []):
            pets.copy_to(out, col, dst)
        plan.append(_plan_row(name, col, roles.get(col, ""), pet, params, cs["reason"], note))
    rowmap = pd.DataFrame({"protected_row": range(len(out)), "original_record_id": df[contract["tables"][name]["record_id"]]})
    return out, rowmap, plan


def load_key(path: Path) -> bytes:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(os.urandom(32))
    return path.read_bytes()


def shuffle(df, rowmap, seed=None):
    """Random row order, so the file order cannot give back the original order (arrival order, for example).
    seed=None draws the permutation from the operating system's cryptographic source."""
    rng = np.random.default_rng(secrets.randbits(128) if seed is None else seed)
    perm = rng.permutation(len(df))
    out = df.iloc[perm].reset_index(drop=True)
    rm = pd.DataFrame({"protected_row": range(len(out)), "original_record_id": rowmap["original_record_id"].iloc[perm].values})
    return out, rm


def repair_released(prot, df, target, order, keys):
    """Repair the protected main table. df: its original rows (aligned with prot); keys(table, column) -> set of
    key values present in another table. Returns (repaired frame, keep mask over the rows, report)."""
    prot = prot.copy()
    # join flags: "this row has rows in table X" is something an attacker of the joined tables knows, so it joins
    # the group key for the repair and is removed again before writing
    flags = []
    for jf in target.get("join_flags", []):
        col = f"_has_{jf['table']}"
        prot[col] = df[jf["on"]].isin(keys(jf["table"], jf["on"])).map({True: "1", False: "0"}).values
        flags.append(col)
    target = {**target, "columns": target["columns"] + flags, "fixed": flags}
    helper = list(flags)
    if target.get("informed"):
        # the informed attacker's extra fact, as a hidden column for the repair only (never released)
        from .checks import sensitive_fact
        prot["_informed"] = sensitive_fact(df[target["sensitive"]])[0].values
        target["informed"] = {**target["informed"], "columns": ["_informed"]}
        helper.append("_informed")
    prot, keep, report = repair.apply(prot, target, order)
    return prot.drop(columns=helper).reset_index(drop=True), keep, report


def protect_folder(contract, original, out, key, labels=None, repair_order=None, seed=None):
    """labels: detect labels frame (table, column, privacy_role); default runs detect on the original folder in memory.
    repair_order: order of the contract's k_target ladder steps (list of step names); None skips the repair.
    Every released table is shuffled (seed only for tests)."""
    original, out = Path(original), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if labels is None:
        labels = detect.detect_dataset(original, original.name)
    plan = []
    for name, spec in contract["tables"].items():
        df = pd.read_csv(original / f"{name}.csv", dtype=str)
        roles = dict(labels[labels.table == name][["column", "privacy_role"]].itertuples(index=False))
        if spec["action"] == "withhold":
            plan += [_plan_row(name, c, roles.get(c, ""), "withhold", None, spec["reason"]) for c in pets.withhold(df.columns)]
            for f in (f"{name}.csv", f"rowmap_{name}.csv"):  # the folder may hold an earlier build of this table
                (out / f).unlink(missing_ok=True)
            continue
        prot, rowmap, rows = protect_table(name, df, contract, key, roles)
        target = contract.get("k_target")
        if repair_order is not None and target and target["table"] == name:
            keys = lambda t, c: set(pd.read_csv(original / f"{t}.csv", dtype=str, usecols=[c])[c].dropna())  # noqa: E731
            prot, keep, report = repair_released(prot, df, target, repair_order, keys)
            rowmap = rowmap[keep.values].reset_index(drop=True)
            rows += repair.plan_rows(name, {**target, "l": target.get("l", 1)}, report)
            (out / "repair_report.json").write_text(json.dumps(report, indent=2) + "\n")
        prot, rowmap = shuffle(prot, rowmap, seed)
        prot.to_csv(out / f"{name}.csv", index=False)
        rowmap.to_csv(out / f"rowmap_{name}.csv", index=False)
        plan += rows
    for f in sorted(original.glob("*.csv")):
        if f.stem not in contract["tables"]:
            plan.append(_plan_row(f.stem, "(all columns)", "", "not released", None, "not in contract, not released"))
    plan = pd.DataFrame(plan)
    plan.to_csv(out / "plan.csv", index=False)
    lines = ["| " + " | ".join(plan.columns) + " |", "|" + "---|" * len(plan.columns)]
    lines += ["| " + " | ".join(str(v).replace("|", "/") for v in r) + " |" for r in plan.itertuples(index=False)]
    (out / "plan.md").write_text("\n".join(lines) + "\n")
    return plan
