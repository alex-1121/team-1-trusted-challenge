"""Run from the repository root with its .venv Python.

Use OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1.
Inputs are restored synthetic proving-ground data and committed contracts.
Only aggregate JSON evidence is written beside this script.
"""
import json
from pathlib import Path

import pandas as pd

from pets_eval.utility.health import u3_admission_model
from pets_eval.utility.education import _features, _fit_auc, _test_mask, u2_dropout_model
from pets_transformer.protect import protect_table


OUTPUT = Path(__file__).parent
PG = Path("data/proving-ground")


def tables(path):
    return {f.stem: pd.read_csv(f, dtype=str) for f in path.glob("*.csv")}


def protected(original, scenario):
    contract = json.loads(Path(f"contracts/generated/{scenario}.auto.json").read_text())
    assert "k_target" not in contract, "This reproduction requires the audited contracts without repair."
    return {
        name: protect_table(name, original[name], contract, b"a" * 32)[0]
        for name, spec in contract["tables"].items()
        if spec["action"] == "release"
    }


def write(name, value):
    (OUTPUT / name).write_text(json.dumps(value, indent=2) + "\n")


health = {"ed_visits": pd.read_csv(PG / "data/health/ed_visits.csv", dtype=str)}
health_holdout = pd.read_csv(PG / "holdout/health/ed_visits.csv", dtype=str)
health_protected = protected(health, "HEALTH-S3")
write("health-s3-independent-utility.json", {
    "original_rows": len(health["ed_visits"]),
    "protected_rows": len(health_protected["ed_visits"]),
    "holdout_rows": len(health_holdout),
    "known_overlap": u3_admission_model(health, health_protected),
    "heldout": u3_admission_model({**health, "holdout__ed_visits": health_holdout}, health_protected),
})

education = tables(PG / "data/education")
education_holdout = tables(PG / "holdout/education")
education_protected = protected(education, "EDU-S2")
original_features, protected_features, holdout_features = map(
    _features, [education, education_protected, education_holdout]
)
original_targets = (education["students"].status == "dropped_out").astype(int).values
protected_targets = (education_protected["students"].status == "dropped_out").astype(int).values
holdout_targets = (education_holdout["students"].status == "dropped_out").astype(int).values
# protect_table preserves row order and row count. This keeps the original test
# identities out of protected training even after their IDs have been tokenised.
assert len(education["students"]) == len(education_protected["students"])
test = _test_mask(education["students"].student_id).values
original_auc = _fit_auc(original_features[~test], original_targets[~test], original_features[test], original_targets[test])
protected_auc = _fit_auc(protected_features[~test], protected_targets[~test], original_features[test], original_targets[test])
holdout_original_auc = _fit_auc(original_features, original_targets, holdout_features, holdout_targets)
holdout_protected_auc = _fit_auc(protected_features, protected_targets, holdout_features, holdout_targets)
write("edu-s2-independent-utility.json", {
    "original_rows": len(original_features),
    "protected_rows": len(protected_features),
    "original_test_rows": int(test.sum()),
    "known_overlap": u2_dropout_model(education, education_protected),
    "identity_aligned_test": {
        "auc_original": original_auc,
        "auc_protected": protected_auc,
        "retention": min(1, (protected_auc - .5) / (original_auc - .5)),
    },
    "heldout": {
        "test_rows": len(holdout_features),
        "auc_original": holdout_original_auc,
        "auc_protected": holdout_protected_auc,
        "retention": min(1, (holdout_protected_auc - .5) / (holdout_original_auc - .5)),
    },
})

overlap = {}
for domain, original, holdout, identifiers in [
    ("health", health["ed_visits"], health_holdout, ["visit_id", "patient_hetu"]),
    ("education", education["students"], education_holdout["students"], ["student_id", "hetu"]),
]:
    overlap[domain] = {
        column: len(set(original[column].dropna()) & set(holdout[column].dropna()))
        for column in identifiers
    }
    assert not any(overlap[domain].values()), "Independent test contains training identities."
write("independent-identity-overlap.json", overlap)
