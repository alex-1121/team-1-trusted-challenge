import json
from pathlib import Path

REQUIRED = ("recipient", "purpose", "trust_level", "threat_model", "required_tasks", "tables", "columns")
PETS = {"pseudonym", "token", "drop", "hour_of_day", "age_band", "top_n_exact_else_other", "keep",
        "month", "week", "day", "round_decimals", "prefix"}


def load(path) -> dict:
    c = json.loads(Path(path).read_text())
    missing = [k for k in REQUIRED if k not in c]
    if missing:
        raise ValueError(f"contract missing keys: {missing}")
    for t, spec in c["tables"].items():
        if spec.get("action") not in ("release", "withhold") or not spec.get("reason"):
            raise ValueError(f"table {t}: action must be release or withhold, with a reason")
        if spec["action"] == "release":
            if "record_id" not in spec or (t not in c["columns"] and t not in c.get("roles", {})):
                raise ValueError(f"released table {t} needs record_id and a columns or roles entry")
            rules = {**{f"column {k}": v for k, v in c["columns"].get(t, {}).items()},
                     **{f"role {k}": v for k, v in c.get("roles", {}).get(t, {}).items()}}
            for what, cs in rules.items():
                if cs.get("pet") not in PETS or not cs.get("reason"):
                    raise ValueError(f"{t} {what}: unknown pet or missing reason")
    kt = c.get("k_target")
    if kt:
        for need in ("table", "k", "columns", "ladder", "reason"):
            if need not in kt:
                raise ValueError(f"k_target missing {need}")
        for name, step in kt["ladder"].items():
            if step.get("op") not in ("widen_band", "widen_hour", "set", "round", "prefix", "to_month") or step.get("column") not in kt["columns"] or not step.get("reason"):
                raise ValueError(f"k_target ladder step {name}: op, a k column and a reason are required")
    return c
