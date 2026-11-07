"""One command: detect, search the repair order, protect, score, run the checks and the red team, and assemble
pets_submission/ only when the red-team gate passes."""
import json
import shutil
from pathlib import Path

import pandas as pd

from . import contract as ct
from . import checks, detect, protect, redteam, repair, score

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
    cpath = ROOT / "contracts" / f"{scenario}.json"
    order = None
    if contract.get("k_target"):
        best = repair.search(contract, original, out, results, key, labels,
                             lambda prot, res: score.run(original, prot, scenario, res, None, cpath, pets_eval))
        order = best["order"]
    plan = protect.protect_folder(contract, original, protected, key, labels, repair_order=order)
    shutil.copy(protected / "plan.md", results / "plan.md")
    if (protected / "repair_report.json").exists():
        shutil.copy(protected / "repair_report.json", results / "repair_report.json")

    score.run(original, protected, scenario, results, baseline, cpath, pets_eval)
    checks.run(protected, original, ROOT / "results" / "checks", PG / "truth", ["checks", "--protected", str(protected.relative_to(ROOT) if protected.is_relative_to(ROOT) else protected),
               "--original", "data/proving-ground/data/" + original.name, "--truth", "data/proving-ground/truth", "--out", "results/checks"])
    gate = redteam.run(protected, original, contract, results, PG / "truth", PG / "adversary", label=f"{scenario} build")
    redteam.write(gate, ROOT / "results" / "redteam" / "after.json")
    if gate["gate"] != "pass":
        failed = [k for k, r in gate["attacks"].items() if r["pass"] is False]
        raise SystemExit(f"red-team gate FAILED ({', '.join(failed)}): pets_submission/ not written. See results/redteam/after.json")

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
