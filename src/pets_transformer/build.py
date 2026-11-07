"""One command: detect, search the repair order, protect, score, run the checks and the red team, and assemble
pets_submission/ only when redteam.evaluate passes the release."""
import json
import os
import shutil
from pathlib import Path

import pandas as pd

from . import contract as ct
from . import checks, detect, policy, protect, redteam, repair, score, selector

ROOT = score.ROOT
PG = ROOT / "data" / "proving-ground"
BASELINE_DIR = ROOT / "baseline-scores"
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


def report_review(reports: list[detect.DetectReport], results: Path) -> str:
    """Write detect_mode.json (the detector mode that actually ran, per dataset), type_probs.csv and needs_review.csv
    (names, types and probabilities, no values) to results and return the warning line, or "" when no column is
    flagged. A flag never stops the build."""
    results = Path(results)
    results.mkdir(parents=True, exist_ok=True)
    modes = {r.labels.dataset.iloc[0] if len(r.labels) else str(i): r.mode for i, r in enumerate(reports)}
    (results / "detect_mode.json").write_text(json.dumps({"modes": modes}, indent=1) + "\n")
    print("detector mode: " + ", ".join(f"{d} {m}" for d, m in modes.items()))
    probs = pd.concat([r.type_probs for r in reports], ignore_index=True)
    review = pd.concat([r.needs_review for r in reports], ignore_index=True)
    probs.to_csv(results / "type_probs.csv", index=False)
    review.to_csv(results / "needs_review.csv", index=False)
    return detect.review_warning(review, with_dataset=True)


def run(scenario, original=None, out=None, results=None, submission=None, pets_eval=score.PETS_EVAL, contract_path=None, policy_dir=None,
        semantic=None):
    """scenario names the contract (contracts/<scenario>.json) unless contract_path is given; the organisers'
    scenario id used for scoring and for the policy is the contract's "scenario" key. Refuses unless the scenario's
    signed policy in policy_dir verifies and allows the contract. semantic picks the detector mode ("lexicon",
    "advisor" or "hybrid"; None: env PETS_SEMANTIC, else advisor when the model is installed)."""
    reports = {}

    def detected(folder: Path, name: str) -> detect.DetectReport:
        # one detection per folder, so the selector, the protector and the submission labels all agree
        if folder not in reports:
            reports[folder] = detect.detect_dataset_report(folder, name, semantic)
        return reports[folder]

    cpath = Path(contract_path) if contract_path else ROOT / "contracts" / f"{scenario}.json"
    run_name = f"{scenario.lower()}-build"
    raw = cpath.read_bytes() if cpath.exists() else None  # hashed and parsed from this one read
    contract = ct.parse(raw) if raw is not None else None
    scenario = contract["scenario"] if contract else scenario
    dataset = contract.get("dataset", "health") if contract else selector.pio.get_scenario(scenario, PG)["dataset"]
    original = Path(original or PG / "data" / dataset)
    out = Path(out or ROOT / "out" / run_name)
    results = Path(results or ROOT / "results" / run_name)
    submission = Path(submission or ROOT / "pets_submission")
    unseen_dir = PG / "data" / "unseen"
    baseline = next(BASELINE_DIR.glob(f"{original.name}_{scenario}_*_raw.json"), None) or \
        next(BASELINE_DIR.glob(f"{original.name.replace('_', '-')}_{scenario}_*_raw.json"), None)
    for need, ok in ((original, original.is_dir()), (unseen_dir, unseen_dir.is_dir() and any(unseen_dir.glob("*.csv"))), (BASELINE_DIR / f"{original.name}_{scenario}_*_raw.json", baseline)):
        if not ok:
            raise FileNotFoundError(f"build needs {need}")
    for name in ("release_record.json", "redteam.json"):  # a refusal from here on must leave no earlier verdict behind
        (results / name).unlink(missing_ok=True)
    pol, pol_sha, signature, fingerprint = policy.verify(policy_dir or policy.DEFAULT_DIR, scenario)
    if contract:
        contract_sha = policy.check_contract(pol, raw)
    else:
        # no reviewed contract yet: the selector writes one from the detected labels and the scenario's tasks, and it
        # has to come out as the contract the steward signed for; a refused one must not replace that file
        c, evidence = selector.select(original, scenario, PG, labels=detected(original, original.name).labels)
        raw = (json.dumps(c, indent=2, ensure_ascii=False) + "\n").encode()
        contract_sha = policy.check_contract(pol, raw)
        cpath = ROOT / "contracts" / "generated" / f"{scenario}.auto.json"
        cpath.parent.mkdir(parents=True, exist_ok=True)
        cpath.write_bytes(raw)
        results.mkdir(parents=True, exist_ok=True)
        (results / "selection.json").write_text(json.dumps(evidence, indent=2) + "\n")
        contract = ct.parse(raw)
    results.mkdir(parents=True, exist_ok=True)

    labels = detected(original, original.name).labels
    unseen = detected(unseen_dir, "unseen").labels[["column", "privacy_role", "subtype"]]
    if line := report_review([detected(original, original.name), detected(unseen_dir, "unseen")], results):
        print(line)

    protected = out / original.name
    # A fresh key for every build: tokens from two releases cannot be joined. It lives in memory only, so no key
    # file exists to leak; any file an earlier build left behind is removed.
    out.mkdir(parents=True, exist_ok=True)
    (out / "hmac.key").unlink(missing_ok=True)
    key = os.urandom(32)
    order = None
    if contract.get("k_target"):
        best = repair.search(contract, original, out, results, key, labels,
                             lambda prot, res: score.run(original, prot, scenario, res, None, cpath, pets_eval), policy_floor=pol["utility_floor"])
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
    gate = redteam.run(protected, original, contract, results, pol["attack_thresholds"], PG / "truth", PG / "adversary", label=f"{run_name} ({rel(cpath)})",
                       specs_path=PG / "metadata" / "attack_specs.json")
    required = (selector.pio.get_scenario(scenario, PG) or {}).get("utility_requirements")
    csvs = sorted(str(f.relative_to(protected)) for f in protected.rglob("*.csv"))
    gate.update(redteam.evaluate(pol, contract, gate, card, check_results, card.get("scan"), csvs, required))
    redteam.write(gate, results / "redteam.json")
    if gate["gate"] != "pass":
        raise SystemExit(f"red-team gate FAILED ({'; '.join(gate['reasons'])}): pets_submission/ not written. See {rel(results / 'redteam.json')}")

    health = submission / original.name
    released = [f"{original.name}/{n}" for n in redteam.expected_files(contract)] + ["unseen_field_labels.csv", f"{original.name}_field_labels.csv"]
    allowed = {*released, "release_record.json", original.name}
    extra = sorted(str(p.relative_to(submission)) for p in submission.rglob("*") if str(p.relative_to(submission)) not in allowed) if submission.exists() else []
    if extra:
        raise SystemExit(f"submission folder {rel(submission)} holds files outside this release: {', '.join(extra)}. "
                         "Nothing was copied or deleted; move them away and build again")
    health.mkdir(parents=True, exist_ok=True)
    for f in released:
        (submission / f).unlink(missing_ok=True)
    for name in redteam.expected_files(contract):
        shutil.copy(protected / name, health / name)
    unseen.to_csv(submission / "unseen_field_labels.csv", index=False)
    labels.to_csv(submission / f"{original.name}_field_labels.csv", index=False)
    rec = policy.record(pol, pol_sha, signature, fingerprint, contract_sha, {f: policy.sha256((submission / f).read_bytes()) for f in released}, check_results, gate)
    for folder in (submission, results):
        (folder / "release_record.json").write_text(json.dumps(rec, indent=2) + "\n")
    return plan
