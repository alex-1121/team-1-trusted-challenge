import argparse
import os
import sys
from pathlib import Path

import pandas as pd

from . import build, checks, contract, policy, protect, redteam, score, selector


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pets_transformer")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("protect", help="apply a contract to a folder of tables")
    p.add_argument("--contract", required=True)
    p.add_argument("--original", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--key-file", help="HMAC key file outside --out; created with 32 random bytes if missing (default: new key per run, not saved)")
    p.add_argument("--labels", help="detect labels csv (dataset,table,column,privacy_role,subtype); default: run detect on --original")
    b = sub.add_parser("build", help="detect, protect, score and assemble pets_submission/ in one go")
    b.add_argument("--scenario", required=True)
    b.add_argument("--original", help="default: data/proving-ground/data/health")
    b.add_argument("--out", help="default: out/<scenario>-build")
    b.add_argument("--results", help="default: results/<scenario>-build")
    b.add_argument("--submission", help="default: pets_submission at the repo root")
    b.add_argument("--pets-eval", default=score.PETS_EVAL)
    b.add_argument("--contract", help="contract JSON (default: contracts/<scenario>.json)")
    b.add_argument("--semantic", choices=["lexicon", "advisor", "hybrid"], default=None,
                   help="detector: word lists only; word lists with the model flagging columns for review (advisor); or "
                        "word lists then the model labels the rest (hybrid). Default: env PETS_SEMANTIC, else advisor "
                        "when the model is installed")
    b.add_argument("--policy-dir", default=policy.DEFAULT_DIR, help="folder with <scenario>.policy.json and its .sig (default: policy/); allowed_signers is always policy/allowed_signers")
    q = sub.add_parser("score", help="run the organisers' scorecard and check, write a summary")
    q.add_argument("--original", required=True)
    q.add_argument("--protected", required=True)
    q.add_argument("--scenario", required=True)
    q.add_argument("--out", required=True)
    q.add_argument("--baseline", help="scorecard JSON of the raw copy (B0)")
    q.add_argument("--contract", help="contract JSON; optional k_columns key sets our own k columns")
    q.add_argument("--pets-eval", default=score.PETS_EVAL)
    q.add_argument("--proving-ground", default=score.PROVING_GROUND)
    k = sub.add_parser("checks", help="l-diversity, informed attacker and joined-table k: checks the scorecard does not run")
    k.add_argument("--protected", required=True)
    k.add_argument("--original", required=True)
    k.add_argument("--out", required=True)
    k.add_argument("--contract", required=True, help="contract JSON with a k_target (table, k columns, sensitive column, join flags)")
    k.add_argument("--truth", help="truth/ folder; attacker rows are the visits in health__ed_visits.csv (default: every original visit)")
    r = sub.add_parser("redteam", help="attacks the scorecard does not run, with a pass/fail gate")
    r.add_argument("--protected", required=True)
    r.add_argument("--original", required=True)
    r.add_argument("--contract", required=True)
    r.add_argument("--out", required=True, help="JSON file to write")
    r.add_argument("--truth", help="truth/ folder (for the news-clip linkage score)")
    r.add_argument("--adversary", help="adversary/ folder (for the news-clip linkage)")
    r.add_argument("--label", default="")
    r.add_argument("--attack-specs", help="metadata/attack_specs.json (for the band-aware scorer linkage)")
    r.add_argument("--policy-dir", default=policy.DEFAULT_DIR, help="folder with <scenario>.policy.json, for the thresholds (default: policy/)")
    s = sub.add_parser("select", help="write a scenario contract from detected labels and the scenario's required tasks (ablation)")
    s.add_argument("--scenario", required=True)
    s.add_argument("--original", help="dataset folder (default: the scenario's dataset in the proving ground)")
    s.add_argument("--proving-ground", default=score.PROVING_GROUND)
    s.add_argument("--out", required=True, help="contract JSON to write")
    s.add_argument("--evidence", help="ablation evidence JSON to write")
    a = ap.parse_args(argv)
    if a.cmd == "protect":
        c = contract.load(a.contract)
        if a.key_file and Path(a.out).resolve() in Path(a.key_file).resolve().parents:
            ap.error("--key-file must not sit inside --out: the out folder is the release")
        key = protect.load_key(Path(a.key_file)) if a.key_file else os.urandom(32)
        labels = pd.read_csv(a.labels, dtype=str) if a.labels else None
        plan = protect.protect_folder(c, a.original, a.out, key, labels)
        print(f"wrote {len(plan)} plan rows to {a.out}")
    elif a.cmd == "build":
        plan = build.run(a.scenario, a.original, a.out, a.results, a.submission, a.pets_eval, a.contract, a.policy_dir,
                         semantic=a.semantic)
        print(f"built {a.scenario}: {len(plan)} plan rows, results in {a.results or 'results/' + a.scenario.lower() + '-build'}")
    elif a.cmd == "checks":
        checks.run(a.protected, a.original, a.out, a.truth, sys.argv[1:] if argv is None else argv, contract.load(a.contract))
        print(f"wrote checks to {a.out}")
    elif a.cmd == "select":
        import json
        pg = Path(a.proving_ground)
        original = Path(a.original or pg / "data" / selector.pio.get_scenario(a.scenario, pg)["dataset"])
        c, ev = selector.select(original, a.scenario, pg)
        for path, obj in ((a.out, c), (a.evidence, ev)):
            if path:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
        print(f"wrote {a.out}")
    elif a.cmd == "redteam":
        c = contract.load(a.contract)
        rep = redteam.run(a.protected, a.original, c, Path(a.out).parent, policy.load(a.policy_dir, c["scenario"])["attack_thresholds"],
                          a.truth, a.adversary, a.label, a.attack_specs)
        redteam.write(rep, a.out)
        print(f"gate {rep['gate']}: " + ", ".join(f"{k} {redteam.shown(v)}" for k, v in rep["attacks"].items()))
    else:
        score.run(a.original, a.protected, a.scenario, a.out, a.baseline, a.contract, a.pets_eval, a.proving_ground)
        print(f"wrote score results to {a.out}")


if __name__ == "__main__":
    main()
