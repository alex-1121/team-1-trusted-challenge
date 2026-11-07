import argparse
import os
from pathlib import Path

from . import contract, protect


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pets_transformer")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("protect", help="apply a contract to a folder of tables")
    p.add_argument("--contract", required=True)
    p.add_argument("--original", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--key-file", help="HMAC key file outside --out; created with 32 random bytes if missing (default: new key per run, not saved)")
    a = ap.parse_args(argv)
    if a.cmd == "protect":
        c = contract.load(a.contract)
        if a.key_file and Path(a.out).resolve() in Path(a.key_file).resolve().parents:
            ap.error("--key-file must not sit inside --out: the out folder is the release")
        key = protect.load_key(Path(a.key_file)) if a.key_file else os.urandom(32)
        plan = protect.protect_folder(c, a.original, a.out, key)
        print(f"wrote {len(plan)} plan rows to {a.out}")


if __name__ == "__main__":
    main()
