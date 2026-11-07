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
    "month": {"quasi_identifier"}, "week": {"quasi_identifier"}, "day": {"quasi_identifier"},
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
        if pet == "pseudonym":
            out[col] = pets.hmac_pseudonym(df[col], key)
        elif pet == "token":
            out[col] = pets.token(df[col], key, params.get("prefix", "T"))
        elif pet == "drop":
            out = pets.drop(out, col)
        elif pet == "hour_of_day":
            out[col] = pets.hour_of_day(df[col], params.get("block", 1))
        elif pet == "age_band":
            out[col] = pets.age_band(df[col], params.get("width", 10))
        elif pet in ("month", "week", "day"):
            out[col] = getattr(pets, pet)(df[col])
        elif pet == "round_decimals":
            out[col] = pets.round_decimals(df[col], params["decimals"])
        elif pet == "prefix":
            out[col] = pets.prefix(df[col], params["n"])
        elif pet == "top_n_exact_else_other":
            out[col] = pets.top_n_exact_else_other(df[col], params["n"])
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
            continue
        prot, rowmap, rows = protect_table(name, df, contract, key, roles)
        target = contract.get("k_target")
        if repair_order is not None and target and target["table"] == name:
            # join flags: "this row has rows in table X" is something an attacker of the joined tables knows,
            # so it joins the group key for the repair and is removed again before writing
            flags = []
            for jf in target.get("join_flags", []):
                other = pd.read_csv(original / f"{jf['table']}.csv", dtype=str, usecols=[jf["on"]])
                col = f"_has_{jf['table']}"
                prot[col] = df[jf["on"]].isin(set(other[jf["on"]].dropna())).map({True: "1", False: "0"}).values
                flags.append(col)
            target = {**target, "columns": target["columns"] + flags, "fixed": flags}
            prot, keep, report = repair.apply(prot, target, repair_order)
            prot = prot.drop(columns=flags)
            rowmap = rowmap[keep.values].reset_index(drop=True)
            prot = prot.reset_index(drop=True)
            rows += repair.plan_rows(name, target, report)
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
