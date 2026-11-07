"""One command: detect, search the repair order, protect, score, run the checks and the red team, and assemble
pets_submission/ only when redteam.evaluate passes the release."""
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
CHECK_FILES = ("l_diversity.json", "informed_attacker.json", "joined_k.json", "not_run.txt")


def run_checks(contract, protected, original, results, argv):
    """What this run's checks produced, file name -> object. results/ is reused, so the gate gets this and never
    reads the folder, and the leftovers of an earlier run go first."""
    out = results / "checks"
    out.mkdir(parents=True, exist_ok=True)
    for name in CHECK_FILES:
        (out / name).unlink(missing_ok=True)
    try:  # the three extra checks read the contract's k target
        return checks.run(protected, original, out, PG / "truth", argv, contract)
    except KeyError as e:
        (out / "not_run.txt").write_text(f"Checks not run: {e.args[0]}.\n")
        return {}


def run(scenario, original=None, out=None, results=None, submission=None, pets_eval=score.PETS_EVAL, contract_path=None):
    """scenario names the contract (contracts/<scenario>.json) unless contract_path is given; the organisers'
    scenario id used for scoring is the contract's "scenario" key, else the same name."""
    cpath = Path(contract_path) if contract_path else ROOT / "contracts" / f"{scenario}.json"
    run_name = f"{scenario.lower()}-build"
    if not cpath.exists():
        # no reviewed contract yet: the selector writes one from the detected labels and the scenario's tasks
        sel_original = Path(original or PG / "data" / selector.pio.get_scenario(scenario, PG)["dataset"])
        c, evidence = selector.select(sel_original, scenario, PG)
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

    labels = detect.detect_dataset(original, original.name)
    unseen = detect.detect_dataset(unseen_dir, "unseen")[["column", "privacy_role", "subtype"]]

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
    check_results = run_checks(contract, protected, original, results, ["checks", "--protected", rel(protected),
                               "--original", "data/proving-ground/data/" + original.name, "--contract", rel(cpath), "--truth", "data/proving-ground/truth",
                               "--out", rel(results / "checks")])
    gate = redteam.run(protected, original, contract, results, PG / "truth", PG / "adversary", label=f"{run_name} ({rel(cpath)})",
                       specs_path=PG / "metadata" / "attack_specs.json")
    required = (selector.pio.get_scenario(scenario, PG) or {}).get("utility_requirements")
    csvs = sorted(str(f.relative_to(protected)) for f in protected.rglob("*.csv"))
    gate.update(redteam.evaluate(contract, gate, card, check_results, card.get("scan"), csvs, required, UTILITY_FLOOR))
    redteam.write(gate, results / "redteam.json")
    if gate["gate"] != "pass":
        raise SystemExit(f"red-team gate FAILED ({'; '.join(gate['reasons'])}): pets_submission/ not written. See {rel(results / 'redteam.json')}")

    health = submission / original.name
    health.mkdir(parents=True, exist_ok=True)
    for f in health.glob("*.csv"):
        f.unlink()
    for name in redteam.expected_files(contract):
        shutil.copy(protected / name, health / name)
    unseen.to_csv(submission / "unseen_field_labels.csv", index=False)
    labels.to_csv(submission / f"{original.name}_field_labels.csv", index=False)
    return plan
