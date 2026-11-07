"""Task 0 baseline: k<5 share of the ed_visits rows over knowable columns, raw table vs the shipped HEALTH-S1 release.

Run: .venv/bin/python scripts/risk_baseline.py [scratch_dir]
Labels come from detect.detect_dataset on the original folder, exactly as build.py does (not the committed csv).
The release is rebuilt with protect.protect_folder using the repair order stored as "chosen" in
results/health-s1-build/repair_search.json; the key and the shuffle do not affect group sizes.
Output goes to a scratch folder, never to data/ or pets_submission/.
"""
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from pets_transformer import contract as ct, detect, protect  # noqa: E402

TABLE, K, MANY = "ed_visits", 5, 50
ORIGINAL = ROOT / "data" / "proving-ground" / "data" / "health"
CATALOG = ROOT / "data" / "proving-ground" / "metadata" / "field_catalog.csv"
KEYED = {"token", "pseudonym"}


def split_columns(raw, spec, labels):
    """Return (knowable, excluded {col: reason}) over the original column names of the table."""
    lab = labels[labels.table == TABLE].set_index("column")
    knowable, excluded = [], {}
    for c in raw.columns:
        pet = spec[c]["pet"]
        sub, role = lab.at[c, "subtype"], lab.at[c, "privacy_role"]
        num = pd.to_numeric(raw[c], errors="coerce")
        numeric = num.notna().mean() >= 0.9 and num.nunique() > MANY
        if pet == "drop":
            excluded[c] = "dropped by the contract"
        elif pet in KEYED:
            excluded[c] = "keyed token"
        elif role == "free_text":
            excluded[c] = "free text"
        elif sub == "MEASUREMENT":
            excluded[c] = "numerical measurement (detector subtype MEASUREMENT)"
        elif numeric:
            excluded[c] = f"numerical measurement (numeric, {num.nunique()} distinct values; detector subtype {sub})"
        else:
            knowable.append(c)
    return knowable, excluded


def share(df, cols):
    sizes = df.groupby(cols, dropna=False)[cols[0]].transform("size")
    return float((sizes < K).mean())


def main():
    scratch = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp())
    contract = ct.load(ROOT / "contracts" / "HEALTH-S1.json")
    labels = detect.detect_dataset(ORIGINAL, ORIGINAL.name)
    search = json.loads((ROOT / "results" / "health-s1-build" / "repair_search.json").read_text())
    order = next(o["order"] for o in search["orders"] if o["name"] == search["chosen"])
    protect.protect_folder(contract, ORIGINAL, scratch / "health", b"k" * 32, labels, repair_order=order)

    raw = pd.read_csv(ORIGINAL / f"{TABLE}.csv", dtype=str)
    prot = pd.read_csv(scratch / "health" / f"{TABLE}.csv", dtype=str)
    spec = contract["columns"][TABLE]
    knowable, excluded = split_columns(raw, spec, labels)
    # a released column may carry another name (also_as copies, duration); a knowable source column stands for them
    released = [c for c in prot.columns if c in knowable
                or any(c in spec[s].get("params", {}).get("also_as", []) for s in knowable)]
    cat = pd.read_csv(CATALOG)
    qi = cat[(cat.dataset == "health") & (cat.table == TABLE) & (cat.privacy_role == "quasi_identifier")].column.tolist()
    qi_rel = [c for c in qi if c in prot.columns]

    print("knowable (raw names):", ", ".join(knowable))
    print("released knowable columns:", ", ".join(released))
    print("excluded:")
    for c, why in excluded.items():
        print(f"  {c}: {why}")
    print("catalogued QIs:", ", ".join(qi), "| still in release:", ", ".join(qi_rel))
    print()
    print(f"{'table':10} {'column set':20} {'release':10} {'n rows':>7} {'k<5 share':>10}")
    for rel, df, ks, qs in (("raw", raw, knowable, qi), ("protected", prot, released, qi_rel)):
        print(f"{TABLE:10} {'knowable':20} {rel:10} {len(df):>7} {share(df, ks):>10.4f}")
        print(f"{TABLE:10} {'catalogued QIs (' + str(len(qs)) + ')':20} {rel:10} {len(df):>7} {share(df, qs):>10.4f}")


main()
