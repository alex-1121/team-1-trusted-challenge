"""Repair: local recoding of the rows that are still at risk after protect.

A row is at risk when its group (rows sharing the contract's k columns) has fewer than k rows, or fewer than l
distinct values of the sensitive column (l-diversity: a group where everyone has the same diagnosis reveals it).
Only those rows are coarsened, one ladder step at a time, re-measuring after every step; rows still at risk after
the ladder get every k column suppressed, and rows still at risk after that are dropped. The order of the ladder
steps changes which utility is lost, so `search` scores every order with the organisers' scorecard and keeps the best.
"""
import itertools
import json
from pathlib import Path

import pandas as pd

from .generalise import BLOCK, SUPPRESSED, hour_block


def at_risk(df, target):
    cols = target["columns"]
    d = df[cols].fillna("")
    g = d.groupby(cols, dropna=False)
    small = g[cols[0]].transform("size") < target["k"]
    inf = target.get("informed")
    if inf:  # an attacker who also knows the sensitive fact (diagnosis group) must still find at least inf["k"] rows
        e = df[cols + inf["columns"]].fillna("")
        small = small | (e.groupby(cols + inf["columns"], dropna=False)[cols[0]].transform("size") < inf["k"])
    sens = target.get("sensitive")
    if sens and target.get("l", 1) > 1:
        low_l = df[sens].fillna("").groupby([d[c] for c in cols], dropna=False).transform("nunique") < target["l"]
        return small | low_l
    return small


def _widen_band(v, width):
    if not isinstance(v, str) or not v[:1].isdigit():
        return v
    lo = int(v.split("-")[0].rstrip("+"))
    if v.endswith("+") or lo >= 80:
        return "80+"
    lo = lo // width * width
    return "80+" if lo >= 80 else f"{lo}-{min(lo + width - 1, 79)}"


def _widen_hour(v, block):
    """"07:00" -> "06:00 to 08:59" for block 3: an explicit range, so the release never shows a block as an exact hour."""
    if not isinstance(v, str) or not v[:2].isdigit():
        return v
    m = BLOCK.match(v)
    if m and int(m.group(2)) - int(m.group(1)) + 1 >= block:
        return v
    return hour_block(int(v[:2]), block)


def _op(series, step):
    op = step["op"]
    if op == "widen_band":
        return series.map(lambda v: _widen_band(v, step["width"]))
    if op == "widen_hour":
        return series.map(lambda v: _widen_hour(v, step["block"]))
    if op == "set":
        return pd.Series(step["value"], index=series.index)
    if op == "round":
        v = pd.to_numeric(series, errors="coerce")
        return v.round(step["decimals"]).map(lambda x: f"{x:.{step['decimals']}f}" if x == x else SUPPRESSED)
    if op == "prefix":
        return series.astype(str).str[:step["n"]]
    if op == "to_day":
        return series.map(lambda v: v[:10] if isinstance(v, str) and len(v) > 10 and v[:4].isdigit() and v[4] == "-" and v[7] == "-" else v)
    if op == "to_month":
        return series.map(lambda v: v[:7] if isinstance(v, str) and len(v) >= 7 and v[:4].isdigit() and v[4] == "-" and v[5:7].isdigit() else v)
    raise ValueError(f"unknown repair op {op!r}")


def _share(mask):
    return round(float(mask.mean()), 4) if len(mask) else 0.0


def apply(df, target, order):
    """Returns (protected frame, keep mask over the input rows, report)."""
    df = df.astype(object)  # pandas string dtype refuses mixed assignment; values stay strings or missing
    linked = target.get("linked", {})
    before = at_risk(df, target)
    report = {"order": list(order), "rows": int(len(df)), "at_risk_before": int(before.sum()), "share_at_risk_before": _share(before), "steps": []}
    for name in order:
        step = target["ladder"][name]
        m = at_risk(df, target)
        col = step["column"]
        df.loc[m, col] = _op(df.loc[m, col], step)
        for dst in linked.get(col, []):
            df.loc[m, dst] = df.loc[m, col]
        report["steps"].append({"step": name, "column": col, "rows_changed": int(m.sum())})
    m = at_risk(df, target)
    fixed = set(target.get("fixed", [])) | set((target.get("informed") or {}).get("columns", []))  # facts the attacker knows from elsewhere (join flags): never suppressed
    for col in [c for c in target["columns"] if c not in fixed]:
        df.loc[m, col] = SUPPRESSED
        for dst in linked.get(col, []):
            df.loc[m, dst] = SUPPRESSED
    report["steps"].append({"step": "suppress", "column": ", ".join(c for c in target["columns"] if c not in fixed), "rows_changed": int(m.sum())})
    m = at_risk(df, target)
    keep = ~m
    report["steps"].append({"step": "drop_rows", "column": "(row)", "rows_changed": int(m.sum())})
    out = df[keep]
    after = at_risk(out, target)
    report.update(rows_released=int(len(out)), at_risk_after=int(after.sum()), share_at_risk_after=_share(after))
    return out, keep, report


def plan_rows(table, target, report):
    rows = []
    for s in report["steps"]:
        step = target["ladder"].get(s["step"], {})
        reason = step.get("reason") or {"suppress": "Rows still at risk after the ladder: every k column suppressed.",
                                        "drop_rows": "Rows still at risk after suppression are not released."}[s["step"]]
        params = {k: v for k, v in step.items() if k not in ("column", "reason")} or ""
        rows.append({"table": table, "column": s["column"], "role": "", "pet": f"repair:{s['step']}", "params": str(params),
                     "reason": reason, "note": f"{s['rows_changed']} rows (only rows in groups with k<{target['k']} or l<{target.get('l', 1)})"})
    return rows


def orders(target, max_full=4):
    """Every order of the ladder steps when there are at most max_full of them (24 orders); beyond that the
    rotations of the contract's order, so the search stays at one scorecard per step. Steps on the same column keep
    the contract's order (a 3-hour block comes before an 8-hour block)."""
    steps = list(target["ladder"])
    col = {s: target["ladder"][s]["column"] for s in steps}

    def keeps_column_order(p):
        return all(p.index(a) < p.index(b) for i, a in enumerate(steps) for b in steps[i + 1:] if col[a] == col[b])
    if len(steps) <= max_full:
        return [list(p) for p in itertools.permutations(steps) if keeps_column_order(p)]
    return [r for r in (steps[i:] + steps[:i] for i in range(len(steps))) if keeps_column_order(r)] or [steps]


def choose(rows, required, floor):
    """rows: dicts with order, tasks, composite, at_risk_after. Best composite among orders whose release has no
    row at risk and every required task at or above the floor; if none clears the floor, best composite of all."""
    ok = [r for r in rows if r["at_risk_after"] == 0]
    good = [r for r in ok if all((r["tasks"].get(t) or 0) >= floor for t in required)] or ok or rows
    return max(good, key=lambda r: r["composite"])


def search(contract, original, out, results, key, labels, score_fn, floor=0.85):
    """score_fn(protected_dir, results_dir) -> scorecard dict. Writes results/repair_search.{json,md}."""
    from . import protect
    target = contract["k_target"]
    rows = []
    for order in orders(target):
        name = "-".join(order)
        prot = Path(out) / "search" / name / Path(original).name
        protect.protect_folder(contract, original, prot, key, labels, repair_order=order)
        card = score_fn(prot, Path(results) / "search" / name)
        rep = json.loads((prot / "repair_report.json").read_text())
        s = card["summary"]
        rows.append({"order": order, "name": name, "tasks": {u["id"]: u["score"] for u in card["utility"]},
                     "privacy": s["privacy"], "utility": s["utility"], "composite": s["composite"],
                     "at_risk_after": rep["at_risk_after"], "rows_released": rep["rows_released"],
                     "steps": rep["steps"]})
    best = choose(rows, contract["required_tasks"], floor)
    Path(results).mkdir(parents=True, exist_ok=True)
    (Path(results) / "repair_search.json").write_text(json.dumps({"target": {k: v for k, v in target.items() if k != "ladder"},
                                                                 "ladder": target["ladder"], "floor": floor,
                                                                 "rule": "best composite among orders with no row at risk and every required task at or above the floor",
                                                                 "chosen": best["name"], "orders": rows}, indent=2) + "\n")
    tids = sorted(rows[0]["tasks"])
    md = ["# Repair search", "", "Every order of the ladder steps was applied by `protect` and scored by the organisers' scorecard "
          "(self-assessment, not the official judging score). Source: `repair_search.json`.", "",
          "| order | " + " | ".join(tids) + " | privacy | utility | composite | rows released | at risk after |",
          "|" + "---|" * (len(tids) + 6)]
    for r in rows:
        md.append(f"| {r['name']}{' (chosen)' if r is best else ''} | " + " | ".join(str(r["tasks"][t]) for t in tids)
                  + f" | {r['privacy']} | {r['utility']} | {r['composite']} | {r['rows_released']} | {r['at_risk_after']} |")
    (Path(results) / "repair_search.md").write_text("\n".join(md) + "\n")
    return best
