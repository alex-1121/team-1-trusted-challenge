import argparse
from pathlib import Path

from . import contract, protect


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pets_transformer")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("protect", help="apply a contract to a folder of tables")
    p.add_argument("--contract", required=True)
    p.add_argument("--original", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--key-file", help="HMAC key file; created with 32 random bytes if missing (default <out>/hmac.key)")
    a = ap.parse_args(argv)
    if a.cmd == "protect":
        c = contract.load(a.contract)
        key = protect.load_key(Path(a.key_file) if a.key_file else Path(a.out) / "hmac.key")
        plan = protect.protect_folder(c, a.original, a.out, key)
        print(f"wrote {len(plan)} plan rows to {a.out}")


if __name__ == "__main__":
    main()
