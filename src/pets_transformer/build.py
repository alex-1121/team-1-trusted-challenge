"""One command: detect, protect, score, and assemble pets_submission/ for a scenario."""
import shutil
from pathlib import Path

import pandas as pd

from . import contract as ct
from . import detect, protect, score

ROOT = score.ROOT
PG = ROOT / "data" / "proving-ground"
BASELINE_DIR = ROOT / "baseline-scores"


def run(scenario, original=None, out=None, results=None, submission=None, pets_eval=score.PETS_EVAL):
    contract = ct.load(ROOT / "contracts" / f"{scenario}.json")
    original = Path(original or PG / "data" / "health")
    run_name = f"{scenario.lower()}-build"
    out = Path(out or ROOT / "out" / run_name)
    results = Path(results or ROOT / "results" / run_name)
    submission = Path(submission or ROOT / "pets_submission")
    unseen_dir = PG / "data" / "unseen"
    baseline = next(BASELINE_DIR.glob(f"{original.name}_{scenario}_*_raw.json"), None)
    for need, ok in ((original, original.is_dir()), (unseen_dir, unseen_dir.is_dir() and any(unseen_dir.glob("*.csv"))), (BASELINE_DIR / f"{original.name}_{scenario}_*_raw.json", baseline)):
        if not ok:
            raise FileNotFoundError(f"build needs {need}")
    results.mkdir(parents=True, exist_ok=True)

    labels = detect.detect_dataset(original, original.name)
    unseen = detect.detect_dataset(unseen_dir, "unseen")[["column", "privacy_role", "subtype"]]

    protected = out / original.name
    # The key sits beside, not inside, the protected folder: that folder is the release.
    key = protect.load_key(out / "hmac.key")
    plan = protect.protect_folder(contract, original, protected, key, labels)
    shutil.copy(protected / "plan.md", results / "plan.md")

    score.run(original, protected, scenario, results, baseline, ROOT / "contracts" / f"{scenario}.json", pets_eval)

    health = submission / original.name
    health.mkdir(parents=True, exist_ok=True)
    for f in health.glob("*.csv"):
        f.unlink()
    for f in protected.glob("*.csv"):
        if f.name != "plan.csv":
            shutil.copy(f, health / f.name)
    unseen.to_csv(submission / "unseen_field_labels.csv", index=False)
    labels.to_csv(submission / f"{original.name}_field_labels.csv", index=False)
    return plan
