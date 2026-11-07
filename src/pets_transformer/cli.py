import argparse
import os
import sys
from pathlib import Path

import pandas as pd

from . import build, checks, contract, protect, redteam, score


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
    k.add_argument("--truth", help="truth/ folder; attacker rows are the visits in health__ed_visits.csv (default: every original visit)")
    r = sub.add_parser("redteam", help="attacks the scorecard does not run, with a pass/fail gate")
    r.add_argument("--protected", required=True)
    r.add_argument("--original", required=True)
    r.add_argument("--contract", required=True)
    r.add_argument("--out", required=True, help="JSON file to write")
    r.add_argument("--truth", help="truth/ folder (for the news-clip linkage score)")
    r.add_argument("--adversary", help="adversary/ folder (for the news-clip linkage)")
    r.add_argument("--label", default="")
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
        plan = build.run(a.scenario, a.original, a.out, a.results, a.submission, a.pets_eval)
        print(f"built {a.scenario}: {len(plan)} plan rows, results in {a.results or 'results/' + a.scenario.lower() + '-build'}")
    elif a.cmd == "checks":
        checks.run(a.protected, a.original, a.out, a.truth, sys.argv[1:] if argv is None else argv)
        print(f"wrote checks to {a.out}")
    elif a.cmd == "redteam":
        rep = redteam.run(a.protected, a.original, contract.load(a.contract), Path(a.out).parent, a.truth, a.adversary, a.label)
        redteam.write(rep, a.out)
        print(f"gate {rep['gate']}: " + ", ".join(f"{k} {v['value']}" for k, v in rep["attacks"].items()))
    else:
        score.run(a.original, a.protected, a.scenario, a.out, a.baseline, a.contract, a.pets_eval, a.proving_ground)
        print(f"wrote score results to {a.out}")


if __name__ == "__main__":
    main()
