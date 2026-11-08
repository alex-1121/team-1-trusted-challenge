"""The signed release policy. The data steward sets the limits of a scenario and signs them; `build` runs only under a
policy whose signature verifies, with a contract the policy allows. Nothing here falls back to a default: every failure
is a refusal.

The principal, the policy folder and the allowed_signers file are fixed here, never read from the policy or from an
argument: a signed file must not choose who may sign it, and an older signed policy kept anywhere else must never be
read, because its signature still verifies.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

from .redteam import ATTACKS, _number
from .score import ROOT

POLICY_DIR = ROOT / "policy"
NAMESPACE = "pets-policy"
PRINCIPAL = "data-steward"
ALLOWED_SIGNERS = POLICY_DIR / "allowed_signers"
VERIFY_TIMEOUT = 30  # seconds
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
    elif type(p["k_min"]) is not int or type(p["l_min"]) is not int or p["k_min"] < 2 or p["l_min"] < 1 or p["no_k_target"]:
        refuse("k_min must be an integer of at least 2 and l_min an integer of at least 1, with no_k_target null")
    if not isinstance(p["allowed_contracts"], dict) or not p["allowed_contracts"].get(p["attacker_assumption"]):
        refuse(f"allowed_contracts has no contract for attacker_assumption {p['attacker_assumption']!r}")
    return p


def _file(scenario):
    return POLICY_DIR / f"{scenario}.policy.json"


def load(scenario):
    """The limits without the signature, for measuring only (`cli redteam`). `build` uses verify."""
    f = _file(scenario)
    if not f.exists():
        refuse(f"no policy file {f}")
    return parse(f.read_bytes(), scenario)


def verify(scenario):
    """Returns (policy, its sha256, the signature's file name, the signing key's fingerprint as ssh-keygen reports it).
    The bytes checked are the bytes parsed: read once, verified on stdin, parsed from the same buffer."""
    f = _file(scenario)
    sig = f.with_name(f.name + ".sig")
    for need in (f, sig, ALLOWED_SIGNERS):
        if not need.exists():
            refuse(f"{need} is missing")
    data = f.read_bytes()
    try:
        r = subprocess.run(["ssh-keygen", "-Y", "verify", "-f", str(ALLOWED_SIGNERS), "-I", PRINCIPAL, "-n", NAMESPACE, "-s", str(sig)],
                           input=data, capture_output=True, timeout=VERIFY_TIMEOUT)
    except subprocess.TimeoutExpired:
        refuse(f"ssh-keygen did not answer within {VERIFY_TIMEOUT} seconds")
    except OSError as e:
        refuse(f"ssh-keygen could not run ({e})")
    if r.returncode:
        refuse(f"the signature of {f.name} does not verify for {PRINCIPAL}: {r.stderr.decode(errors='replace').strip()}")
    key = re.search(r" key (SHA256:\S+)", r.stdout.decode(errors="replace"))
    if not key:
        refuse("ssh-keygen verified the signature but reported no key fingerprint")
    return parse(data, scenario), sha256(data), sig.name, key.group(1)


DRAFT_THRESHOLDS = {"order_attack": 0.05, "news_linkage": 0.0, "person_fingerprint": 0.05, "scorer_linkage_band_aware": 0.01,
                    "plain_hash": 0.0}  # the limits every signed policy in policy/ uses
DRAFT_UTILITY_FLOOR = 0.5


def draft(scen, contract_data):
    """An unsigned policy for a scenario that has none: who and why from the organisers' scenario definition, the
    limits every signed policy here uses, k and l from the contract's k target, and the contract pinned by its sha256.
    A draft for a person to review (and the steward to sign), never a decision: parse() checks it like any other."""
    kt = json.loads(contract_data).get("k_target")
    p = {"scenario": scen["id"], "owner_role": f"{scen['dataset'].replace('_', ' ')} data steward",
         "recipient": scen["recipient"], "purpose": scen["purpose"],
         "agreement_ref": f"none: {scen['id']} is a synthetic proving-ground scenario, no real agreement exists",
         "recipient_duties": ["No re-identification of any person in the release.",
                              "No linkage with outside data about the people in the release."],
         "enforced_after_release": "none", "attack_thresholds": dict(DRAFT_THRESHOLDS), "utility_floor": DRAFT_UTILITY_FLOOR,
         "k_min": kt["k"] if kt else None, "l_min": kt.get("l", 1) if kt else None,
         "no_k_target": None if kt else "The selected contract releases no quasi-identifier, so there is no group to count.",
         "required_tasks": list(scen["utility_requirements"]), "attacker_assumption": "default",
         "allowed_contracts": {"default": sha256(contract_data)}}
    return parse(json.dumps(p).encode(), scen["id"])


def check_contract(policy, data):
    """The contract's sha256 when it is the one allowed for the selected attacker assumption, else a refusal."""
    assumption, got = policy["attacker_assumption"], sha256(data)
    if got != policy["allowed_contracts"][assumption]:
        refuse(f"contract sha256 {got} is not the one allowed for attacker assumption {assumption!r}")
    return got


def record(policy, policy_sha, signature, fingerprint, contract_sha, files, check_results, report):
    """release_record.json: what left, under which signed policy, and what stays at risk. files: path -> sha256 of every
    file in the submission folder; the row maps are listed apart, because they are for the organisers' scoring only."""
    rowmaps = {f: h for f, h in files.items() if Path(f).name.startswith("rowmap_")}
    checks = {n.removesuffix(".json"): o.get("per_join") or o["result"] for n, o in check_results.items()}
    return {"scenario": policy["scenario"], "gate": report["gate"], "policy_sha256": policy_sha, "signature_file": signature,
            "signing_key_fingerprint": fingerprint,
            "attacker_assumption": policy["attacker_assumption"], "contract_sha256": contract_sha,
            "files_for_recipient": {f: h for f, h in files.items() if f not in rowmaps},
            "files_for_organiser_scoring_only": rowmaps,
            "row_maps": "The row maps link each released row to its original record: they go to the organisers for scoring only and never to the recipient.",
            "recipient": policy["recipient"], "purpose": policy["purpose"], "agreement_ref": policy["agreement_ref"],
            "recipient_duties": policy["recipient_duties"], "enforced_after_release": policy["enforced_after_release"],
            "residual_risks": {"checks": checks or f"not run: {policy['no_k_target']}",
                               "attacks_not_applicable": {k: a["reason"] for k, a in report["attacks"].items() if a["status"] == "not_applicable"}}}
