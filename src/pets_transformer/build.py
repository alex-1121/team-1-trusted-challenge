"""One command: detect, search the repair order, protect, score, run the checks and the red team, and assemble
pets_submission/ only when the red-team gate passes."""
import json
import shutil
from pathlib import Path

import pandas as pd

from . import contract as ct
from . import checks, detect, protect, redteam, repair, score, selector

ROOT = score.ROOT
PG = ROOT / "data" / "proving-ground"
BASELINE_DIR = ROOT / "baseline-scores"
UTILITY_FLOOR = 0.5


def report_review(reports: list[detect.DetectReport], results: Path) -> str:
    """Write type_probs.csv and needs_review.csv (names, types and probabilities, no values) to results and return
    the warning line, or "" when no column is flagged. A flag never stops the build."""
    results = Path(results)
    results.mkdir(parents=True, exist_ok=True)
    probs = pd.concat([r.type_probs for r in reports], ignore_index=True)
    review = pd.concat([r.needs_review for r in reports], ignore_index=True)
    probs.to_csv(results / "type_probs.csv", index=False)
    review.to_csv(results / "needs_review.csv", index=False)
    return detect.review_warning(review, with_dataset=True)


def run(scenario, original=None, out=None, results=None, submission=None, pets_eval=score.PETS_EVAL, contract_path=None,
        semantic=None):
    """scenario names the contract (contracts/<scenario>.json) unless contract_path is given; the organisers'
    scenario id used for scoring is the contract's "scenario" key, else the same name. semantic picks the detector
    mode ("lexicon" or "hybrid"; None: env PETS_SEMANTIC, else hybrid when the model is installed)."""
    reports = {}

    def detected(folder: Path, name: str) -> detect.DetectReport:
        # one detection per folder, so the selector, the protector and the submission labels all agree
        if folder not in reports:
            reports[folder] = detect.detect_dataset_report(folder, name, semantic)
        return reports[folder]

    cpath = Path(contract_path) if contract_path else ROOT / "contracts" / f"{scenario}.json"
    run_name = f"{scenario.lower()}-build"
    if not cpath.exists():
        # no reviewed contract yet: the selector writes one from the detected labels and the scenario's tasks
        sel_original = Path(original or PG / "data" / selector.pio.get_scenario(scenario, PG)["dataset"])
        c, evidence = selector.select(sel_original, scenario, PG,
                                      labels=detected(sel_original, sel_original.name).labels)
        cpath = ROOT / "contracts" / "generated" / f"{scenario}.auto.json"
        cpath.parent.mkdir(parents=True, exist_ok=True)
        cpath.write_text(json.dumps(c, indent=2, ensure_ascii=False) + "\n")
        ev = Path(results or ROOT / "results" / run_name) / "selection.json"
        ev.parent.mkdir(parents=True, exist_ok=True)
        ev.write_text(json.dumps(evidence, indent=2) + "\n")
    contract = ct.load(cpath)
    scenario = contract.get("scenario", scenario)
    original = Path(original or PG / "data" / contract.get("dataset", "health"))
    out = Path(out or ROOT / "out" / run_name)
    results = Path(results or ROOT / "results" / run_name)
    submission = Path(submission or ROOT / "pets_submission")
    unseen_dir = PG / "data" / "unseen"
    baseline = next(BASELINE_DIR.glob(f"{original.name}_{scenario}_*_raw.json"), None) or \
        next(BASELINE_DIR.glob(f"{original.name.replace('_', '-')}_{scenario}_*_raw.json"), None)
    for need, ok in ((original, original.is_dir()), (unseen_dir, unseen_dir.is_dir() and any(unseen_dir.glob("*.csv"))), (BASELINE_DIR / f"{original.name}_{scenario}_*_raw.json", baseline)):
        if not ok:
            raise FileNotFoundError(f"build needs {need}")
    results.mkdir(parents=True, exist_ok=True)

    labels = detected(original, original.name).labels
    unseen = detected(unseen_dir, "unseen").labels[["column", "privacy_role", "subtype"]]
    if line := report_review([detected(original, original.name), detected(unseen_dir, "unseen")], results):
        print(line)

    protected = out / original.name
    # A fresh key for every build: tokens from two releases cannot be joined. It sits beside, not inside, the
    # protected folder (that folder is the release) and is never handed over.
    out.mkdir(parents=True, exist_ok=True)
    (out / "hmac.key").unlink(missing_ok=True)
    key = protect.load_key(out / "hmac.key")
    order = None
    if contract.get("k_target"):
        best = repair.search(contract, original, out, results, key, labels,
                             lambda prot, res: score.run(original, prot, scenario, res, None, cpath, pets_eval))
        order = best["order"]
    plan = protect.protect_folder(contract, original, protected, key, labels, repair_order=order)
    shutil.copy(protected / "plan.md", results / "plan.md")
    if (protected / "repair_report.json").exists():
        shutil.copy(protected / "repair_report.json", results / "repair_report.json")

    card = score.run(original, protected, scenario, results, baseline, cpath, pets_eval)
    rel = lambda p: str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)  # noqa: E731
    try:  # the three extra checks read the contract's k target
        checks.run(protected, original, results / "checks", PG / "truth", ["checks", "--protected", rel(protected),
                   "--original", "data/proving-ground/data/" + original.name, "--contract", rel(cpath), "--truth", "data/proving-ground/truth",
                   "--out", rel(results / "checks")], contract)
    except KeyError as e:
        (results / "checks").mkdir(parents=True, exist_ok=True)
        (results / "checks" / "not_run.txt").write_text(f"Checks not run: {e.args[0]}.\n")
    gate = redteam.run(protected, original, contract, results, PG / "truth", PG / "adversary", label=f"{run_name} ({rel(cpath)})",
                       specs_path=PG / "metadata" / "attack_specs.json")
    # utility gate: a release that no longer serves its purpose is refused too
    req = {u["id"]: (u["score"] or 0.0) for u in card["utility"] if u.get("required")}
    low = {k: v for k, v in req.items() if v < UTILITY_FLOOR}
    gate["utility_check"] = {"rule": f"every required task scores at least {UTILITY_FLOOR}", "scores": req,
                             "pass": not low, "below_floor": low}
    if low:
        gate["gate"] = "fail"
    redteam.write(gate, results / "redteam.json")
    if gate["gate"] != "pass":
        failed = [k for k, r in gate["attacks"].items() if r["pass"] is False] + (["utility"] if low else [])
        raise SystemExit(f"red-team gate FAILED ({', '.join(failed)}): pets_submission/ not written. See {rel(results / 'redteam.json')}")

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
