import json
from pathlib import Path

REQUIRED = ("recipient", "purpose", "trust_level", "threat_model", "required_tasks", "tables", "columns")
PETS = {"pseudonym", "drop", "hour_of_day", "age_band", "top_n_exact_else_other", "keep"}


def load(path) -> dict:
    c = json.loads(Path(path).read_text())
    missing = [k for k in REQUIRED if k not in c]
    if missing:
        raise ValueError(f"contract missing keys: {missing}")
    for t, spec in c["tables"].items():
        if spec.get("action") not in ("release", "withhold") or not spec.get("reason"):
            raise ValueError(f"table {t}: action must be release or withhold, with a reason")
        if spec["action"] == "release":
            if "record_id" not in spec or t not in c["columns"]:
                raise ValueError(f"released table {t} needs record_id and a columns entry")
            for col, cs in c["columns"][t].items():
                if cs.get("pet") not in PETS or not cs.get("reason"):
                    raise ValueError(f"{t}.{col}: unknown pet or missing reason")
    return c
