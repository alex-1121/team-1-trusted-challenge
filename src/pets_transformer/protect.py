import os
from pathlib import Path

import pandas as pd

from . import pets


def _plan_row(table, column, pet, params, reason):
    return {"table": table, "column": column, "role": "", "pet": pet, "params": params and str(params) or "", "reason": reason}


def protect_table(name, df, contract, key):
    spec = contract["columns"][name]
    unnamed = [c for c in df.columns if c not in spec]
    if unnamed:
        raise ValueError(f"{name}: columns not in contract: {unnamed}")
    unknown = [c for c in spec if c not in df.columns]
    if unknown:
        raise ValueError(f"{name}: contract names columns not in table: {unknown}")
    out = df.copy()
    plan = []
    for col in df.columns:
        cs = spec[col]
        pet, params = cs["pet"], cs.get("params", {})
        if pet == "pseudonym":
            out[col] = pets.hmac_pseudonym(df[col], key)
        elif pet == "drop":
            out = pets.drop(out, col)
        elif pet == "hour_of_day":
            out[col] = pets.hour_of_day(df[col])
        elif pet == "age_band":
            out[col] = pets.age_band(df[col], params.get("width", 10))
        elif pet == "top_n_exact_else_other":
            out[col] = pets.top_n_exact_else_other(df[col], params["n"])
        for dst in params.get("also_as", []):
            pets.copy_to(out, col, dst)
        plan.append(_plan_row(name, col, pet, params, cs["reason"]))
    rowmap = pd.DataFrame({"protected_row": range(len(out)), "original_record_id": df[contract["tables"][name]["record_id"]]})
    return out, rowmap, plan


def load_key(path: Path) -> bytes:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(os.urandom(32))
    return path.read_bytes()


def protect_folder(contract, original, out, key):
    original, out = Path(original), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    plan = []
    for name, spec in contract["tables"].items():
        df = pd.read_csv(original / f"{name}.csv", dtype=str)
        if spec["action"] == "withhold":
            plan += [_plan_row(name, c, "withhold", None, spec["reason"]) for c in pets.withhold(df.columns)]
            continue
        prot, rowmap, rows = protect_table(name, df, contract, key)
        prot.to_csv(out / f"{name}.csv", index=False)
        rowmap.to_csv(out / f"rowmap_{name}.csv", index=False)
        plan += rows
    plan = pd.DataFrame(plan)
    plan.to_csv(out / "plan.csv", index=False)
    lines = ["| " + " | ".join(plan.columns) + " |", "|" + "---|" * len(plan.columns)]
    lines += ["| " + " | ".join(str(v).replace("|", "/") for v in r) + " |" for r in plan.itertuples(index=False)]
    (out / "plan.md").write_text("\n".join(lines) + "\n")
    return plan
