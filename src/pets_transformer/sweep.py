import argparse
import copy
import functools
import json
import os
import time
from pathlib import Path

import pandas as pd

from . import contract as contract_mod, pets, protect, score

WIDTHS = (5, 10, 20)
BLOCKS = (1, 2, 3)
FLOOR = 0.90
OWN_K_TARGET = 0.05
RULE = (f"Keep the cells where every required task scores at least {FLOOR}. Among them, if any cell has own k<5 share at or below {OWN_K_TARGET}, "
        "take the best composite among those cells. Otherwise take the lowest own k<5 share among the eligible cells that tie on the best composite "
        "(composites compared at 4 decimals). If no cell clears the floor, the same two steps run over all cells.")


def choose(rows, required):
    """rows: dicts with cell, tasks, own_k, composite. Returns the chosen row."""
    # The scorer reports None for a task that errored and counts it as 0 in the composite; do the same here.
    ok = [r for r in rows if all((r["tasks"][t] or 0) >= FLOOR for t in required)] or rows
    low = [r for r in ok if r["own_k"] <= OWN_K_TARGET]
    if low:
        return max(low, key=lambda r: r["composite"])
    best = max(round(r["composite"], 4) for r in ok)
    return min((r for r in ok if round(r["composite"], 4) == best), key=lambda r: r["own_k"])


def patch(c, width, block):
    c = copy.deepcopy(c)
    for col in c["columns"]["ed_visits"].values():
        if col["pet"] == "age_band":
            col.setdefault("params", {})["width"] = width
        elif col["pet"] == "hour_of_day":
            col.setdefault("params", {})["block"] = block
    return c


def run_cell(c, width, block, original, out, results, key):
    cell = f"w{width}_b{block}"
    t0 = time.time()
    prot = Path(out) / cell
    # protect.py calls pets.hour_of_day without params, so the block is bound here for the duration of the cell.
    real = pets.hour_of_day
    pets.hour_of_day = functools.partial(real, block=block)
    try:
        protect.protect_folder(patch(c, width, block), original, prot, key)
    finally:
        pets.hour_of_day = real
    res = Path(results) / cell
    card = score.run(original, prot, "HEALTH-S1", res, contract=None)
    k_cols = c.get("k_columns") or score.K_COLUMNS
    own = score.own_k(pd.read_csv(prot / "ed_visits.csv", dtype=str), k_cols)[0]
    s = card["summary"]
    tasks = {u["id"]: u["score"] for u in card["utility"]}
    scorer_k = card["tables"]["ed_visits"]["k_anonymity"]["share_below"]["k<5"]
    return {"cell": cell, "width": width, "block": block, "tasks": tasks, "scorer_k": scorer_k, "own_k": own,
            "privacy": s["privacy"], "utility": s["utility"], "composite": s["composite"], "seconds": round(time.time() - t0, 1)}


def table(rows, required, chosen, total):
    tids = sorted(rows[0]["tasks"])
    hdr = ["cell (age width, hour block)", *tids, "scorer k<5", "own k<5", "privacy", "utility", "composite", "seconds"]
    out = ["# HEALTH-S1 sweep", "", "Every number is copied from the cell's scorecard.json, except own k<5 and seconds, which `sweep` computes and times. "
           f"{score.LABEL}.", "", "| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for r in rows:
        out.append("| " + " | ".join([f"{r['cell']} ({r['width']}, {r['block']})", *(str(r["tasks"][t]) for t in tids), str(r["scorer_k"]),
                                      f"{r['own_k']:.4f}", str(r["privacy"]), str(r["utility"]), str(r["composite"]), str(r["seconds"])]) + " |")
    out += ["", f"Total runtime: {total:.0f} seconds.", "", "## Rule", "", RULE, "",
            f"Required tasks: {', '.join(required)}. Own k columns: date_of_birth, sex, municipality, arrival_ts.", "",
            "## Chosen cell", "", f"{chosen['cell']}: age band width {chosen['width']} years, arrival hour block {chosen['block']} hours "
            f"(composite {chosen['composite']}, own k<5 {chosen['own_k']:.4f}). The contract is not edited here; the deliverables ticket adopts these parameters.", ""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pets_transformer.sweep")
    ap.add_argument("--contract", required=True)
    ap.add_argument("--original", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--results", required=True)
    a = ap.parse_args(argv)
    c = contract_mod.load(a.contract)
    key = os.urandom(32)
    t0 = time.time()
    rows = [run_cell(c, w, b, a.original, a.out, a.results, key) for w in WIDTHS for b in BLOCKS]
    chosen = choose(rows, c["required_tasks"])
    (Path(a.results) / "sweep.md").write_text(table(rows, c["required_tasks"], chosen, time.time() - t0))
    print(f"chosen {chosen['cell']}")


if __name__ == "__main__":
    main()
