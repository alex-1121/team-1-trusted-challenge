"""The signed release policy. The data steward sets the limits of a scenario and signs them; `build` runs only under a
policy whose signature verifies, with a contract the policy allows. Nothing here falls back to a default: every failure
is a refusal.

The principal is fixed here, not read from the policy: a signed file must not choose who may sign it.
"""
import hashlib
import json
import subprocess
from pathlib import Path

from .redteam import ATTACKS, _number
from .score import ROOT

DEFAULT_DIR = ROOT / "policy"
NAMESPACE = "pets-policy"
PRINCIPAL = "data-steward"
FIELDS = ("scenario", "owner_role", "recipient", "purpose", "agreement_ref", "recipient_duties", "enforced_after_release", "attack_thresholds",
          "utility_floor", "k_min", "l_min", "no_k_target", "required_tasks", "attacker_assumption", "allowed_contracts")


def refuse(why):
    raise SystemExit(f"policy refused: {why}. Nothing was built.")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def parse(data, scenario):
    """The policy in data, refused unless every limit is present and the file is about this scenario."""
    try:
        p = json.loads(data)
    except ValueError as e:
        refuse(f"not valid JSON ({e})")
    missing = [f for f in FIELDS if f not in p] if isinstance(p, dict) else list(FIELDS)
    if missing:
        refuse(f"missing fields {missing}")
    if p["scenario"] != scenario:  # a signed policy of another scenario, renamed
        refuse(f"the file is for {p['scenario']}, not {scenario}")
    t = p["attack_thresholds"]
    if not isinstance(t, dict) or sorted(t) != sorted(ATTACKS) or not all(_number(v) for v in t.values()):
        refuse(f"attack_thresholds must give a number for each of {list(ATTACKS)}")
    if not _number(p["utility_floor"]):
        refuse("utility_floor must be a number")
    if not p["required_tasks"] or not isinstance(p["required_tasks"], list):
        refuse("required_tasks must list at least one task")
    if p["k_min"] is None:
        if p["l_min"] is not None or not p["no_k_target"]:
            refuse("a policy without k_min must say why in no_k_target and have no l_min")
    elif not (isinstance(p["k_min"], int) and isinstance(p["l_min"], int)) or p["no_k_target"]:
        refuse("k_min and l_min must be integers, with no_k_target null")
    if not isinstance(p["allowed_contracts"], dict) or not p["allowed_contracts"].get(p["attacker_assumption"]):
        refuse(f"allowed_contracts has no contract for attacker_assumption {p['attacker_assumption']!r}")
    return p


def _file(policy_dir, scenario):
    return Path(policy_dir) / f"{scenario}.policy.json"


def load(policy_dir, scenario):
    """The limits without the signature, for measuring only (`cli redteam`). `build` uses verify."""
    f = _file(policy_dir, scenario)
    if not f.exists():
        refuse(f"no policy file {f}")
    return parse(f.read_bytes(), scenario)


def verify(policy_dir, scenario):
    """Returns (policy, its sha256, the signature's file name). The bytes checked are the bytes parsed."""
    f = _file(policy_dir, scenario)
    sig, signers = f.with_name(f.name + ".sig"), Path(policy_dir) / "allowed_signers"
    for need in (f, sig, signers):
        if not need.exists():
            refuse(f"{need} is missing")
    data = f.read_bytes()
    try:
        r = subprocess.run(["ssh-keygen", "-Y", "verify", "-f", str(signers), "-I", PRINCIPAL, "-n", NAMESPACE, "-s", str(sig)],
                           input=data, capture_output=True)
    except OSError as e:
        refuse(f"ssh-keygen could not run ({e})")
    if r.returncode:
        refuse(f"the signature of {f.name} does not verify for {PRINCIPAL}: {r.stderr.decode(errors='replace').strip()}")
    return parse(data, scenario), sha256(data), sig.name


def check_contract(policy, data):
    """The contract's sha256 when it is the one allowed for the selected attacker assumption, else a refusal."""
    assumption, got = policy["attacker_assumption"], sha256(data)
    if got != policy["allowed_contracts"][assumption]:
        refuse(f"contract sha256 {got} is not the one allowed for attacker assumption {assumption!r}")
    return got


def record(policy, policy_sha, signature, contract_sha, files, check_results, report):
    """release_record.json: what left, under which signed policy, and what stays at risk. files: path -> sha256."""
    checks = {n.removesuffix(".json"): o.get("per_join") or o["result"] for n, o in check_results.items()}
    return {"scenario": policy["scenario"], "gate": report["gate"], "policy_sha256": policy_sha, "signature_file": signature,
            "attacker_assumption": policy["attacker_assumption"], "contract_sha256": contract_sha, "files_sha256": files,
            "recipient": policy["recipient"], "purpose": policy["purpose"], "agreement_ref": policy["agreement_ref"],
            "recipient_duties": policy["recipient_duties"], "enforced_after_release": policy["enforced_after_release"],
            "residual_risks": {"checks": checks or f"not run: {policy['no_k_target']}",
                               "attacks_not_applicable": {k: a["reason"] for k, a in report["attacks"].items() if a["status"] == "not_applicable"}}}
