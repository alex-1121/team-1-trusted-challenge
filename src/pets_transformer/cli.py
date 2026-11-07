import argparse
import os
from pathlib import Path

import pandas as pd

from . import build, contract, protect, score


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
    q = sub.add_parser("score", help="run the organisers' scorecard and check, write a summary")
    q.add_argument("--original", required=True)
    q.add_argument("--protected", required=True)
    q.add_argument("--scenario", required=True)
    q.add_argument("--out", required=True)
    q.add_argument("--baseline", help="scorecard JSON of the raw copy (B0)")
    q.add_argument("--contract", help="contract JSON; optional k_columns key sets our own k columns")
    q.add_argument("--pets-eval", default=score.PETS_EVAL)
    q.add_argument("--proving-ground", default=score.PROVING_GROUND)
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
        plan = build.run(a.scenario, a.original, a.out, a.results, a.submission)
        print(f"built {a.scenario}: {len(plan)} plan rows, results in {a.results or 'results/' + a.scenario.lower() + '-build'}")
    else:
        score.run(a.original, a.protected, a.scenario, a.out, a.baseline, a.contract, a.pets_eval, a.proving_ground)
        print(f"wrote score results to {a.out}")


if __name__ == "__main__":
    main()
