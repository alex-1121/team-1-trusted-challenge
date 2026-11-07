"""Evaluate the column-type model against the word lists (E1-E5 of plans/2026-11-07-eu-column-types.md).

    python scripts/semantic/evaluate.py --split dev  --out results/detect-semantic
    python scripts/semantic/evaluate.py --split test --out results/detect-semantic   # once, see SPLIT.md
    python scripts/semantic/evaluate.py --cost       --out results/detect-semantic   # E5 timing only

Runs detect in both modes (lexicon, hybrid) and writes, for the split:
  e1_proving_ground_<split>.json  role macro-F1, accuracy, subtype accuracy, per role (organisers' score_detection)
  e2_eu_<split>.json              per fake EU country: macro-F1, model-type columns labelled harmless, other columns
  e2b_unseen.json                 (dev only) every unseen column whose label differs between modes
  e3_calibration_<split>.json     ECE and reliability table on columns of the model's types
  e4_warnings_<split>.json        needs-review count and share per dataset
  e5_cost.json                    (--cost) seconds for detect on all nine proving-ground datasets, both modes

No values are written: only names, labels, probabilities, counts and scores. Every file records the commit, the
encoder revision, the thresholds and the time. The test split refuses to run twice.
"""
import argparse
import inspect
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from pets_eval.detect import score_detection  # noqa: E402

from pets_transformer import detect  # noqa: E402
from pets_transformer.semantic import decide as dec  # noqa: E402
from pets_transformer.semantic.features import sample_values  # noqa: E402
from pets_transformer.semantic.metrics import ece, reliability  # noqa: E402
from pets_transformer.semantic.model import MODEL_DIR, load_model  # noqa: E402
from pets_transformer.semantic.types import TYPES, type_of  # noqa: E402

PG = ROOT / "data" / "proving-ground"
EVAL = ROOT / "data" / "semantic-eval"
CORPUS = ROOT / "data" / "semantic-corpus"
TUNING = ["finance", "cyber", "education", "mobility", "energy", "smart_city"]
HELD_OUT = ["health", "public_admin", "customer_service"]
MODES = ("lexicon", "hybrid")
LABEL_COLS = ["dataset", "table", "column", "privacy_role", "subtype"]
RISKY_TYPES = [t for t in TYPES if t != "CATEGORY"]  # the types E2 counts: harmless is wrong for them


def stamp() -> dict:
    def defaults(f):
        return {k: v.default for k, v in inspect.signature(f).parameters.items() if v.default is not v.empty}
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", "src", "scripts"], cwd=ROOT,
                                capture_output=True, text=True).stdout.strip())
    meta = json.loads((MODEL_DIR / "meta.json").read_text())
    return {"commit": commit, "uncommitted_changes": dirty, "encoder": meta["encoder"], "revision": meta["revision"],
            "head_created": meta["created"], "temperature": meta["temperature"],
            "thresholds": {"decide": defaults(dec.decide), "combine": defaults(dec.combine)},
            "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


def write(out: Path, name: str, body: dict, st: dict) -> None:
    (out / name).write_text(json.dumps({**st, **body}, indent=1, ensure_ascii=False, default=float) + "\n")
    print(f"wrote {out / name}")


def run(folder: Path, dataset: str, mode: str) -> detect.DetectReport:
    return detect.detect_dataset_report(folder, dataset, mode)


def score(labels: pd.DataFrame, catalog: pd.DataFrame, dataset: str) -> dict:
    s = score_detection(labels[LABEL_COLS], catalog, [dataset])
    keep = ("n_fields", "n_predicted", "accuracy", "macro_f1", "sensitive_recall", "subtype_accuracy", "per_role")
    return {k: s[k] for k in keep if k in s}


def warnings(rep: detect.DetectReport) -> dict:
    n = len(rep.labels)
    flags = rep.needs_review["flag"].value_counts().to_dict() if len(rep.needs_review) else {}
    return {"columns": n, "model_read": len(rep.type_probs), "needs_review": len(rep.needs_review),
            "share": round(len(rep.needs_review) / n, 4) if n else 0.0, "by_flag": flags,
            "columns_flagged": [f"{r.table}.{r.column} ({r.flag})" for r in rep.needs_review.itertuples()]}


def changed(a: pd.DataFrame, b: pd.DataFrame, probs: pd.DataFrame) -> list[dict]:
    m = a.merge(b, on=["dataset", "table", "column"], suffixes=("_lexicon", "_hybrid"))
    m = m[(m.privacy_role_lexicon != m.privacy_role_hybrid) | (m.subtype_lexicon != m.subtype_hybrid)]
    flags = {(r.table, r.column): r.flag for r in probs.itertuples()} if len(probs) else {}
    return [{"table": r.table, "column": r.column, "lexicon": f"{r.privacy_role_lexicon} {r.subtype_lexicon}",
             "hybrid": f"{r.privacy_role_hybrid} {r.subtype_hybrid}", "flag": flags.get((r.table, r.column)) or None}
            for r in m.itertuples()]


def e1(datasets: list[str]) -> tuple[dict, dict]:
    catalog = pd.read_csv(PG / "metadata" / "field_catalog.csv", dtype=str)
    body, warn = {"datasets": {}}, {}
    for d in datasets:
        reps = {m: run(PG / "data" / d, d, m) for m in MODES}
        body["datasets"][d] = {m: score(reps[m].labels, catalog, d) for m in MODES}
        body["datasets"][d]["changed"] = changed(reps["lexicon"].labels, reps["hybrid"].labels, reps["hybrid"].type_probs)
        warn[d] = warnings(reps["hybrid"])
        print(d, {m: body["datasets"][d][m]["macro_f1"] for m in MODES}, f"warnings {warn[d]['needs_review']}")
    body["summary"] = {m: {d: body["datasets"][d][m]["macro_f1"] for d in datasets} for m in MODES}
    return body, warn


def model_type(role: str, subtype: str) -> str | None:
    return type_of(role, subtype)


def e2(folder: Path) -> tuple[dict, dict, list[tuple[np.ndarray, int]]]:
    """Per country: macro-F1 both modes; model-type columns labelled harmless; non-model columns separately."""
    catalog = pd.read_csv(folder / "catalog.csv", dtype=str)
    model = load_model()
    body, warn, calib = {"countries": {}}, {}, []
    for loc in sorted(catalog.dataset.unique()):
        cat = catalog[catalog.dataset == loc]
        reps = {m: run(folder / loc, loc, m) for m in MODES}
        row = {m: score(reps[m].labels, catalog, loc) for m in MODES}
        for m in MODES:
            lab = reps[m].labels.merge(cat, on=["dataset", "table", "column"], suffixes=("", "_true"))
            lab["type"] = [model_type(r, s) for r, s in zip(lab.privacy_role_true, lab.subtype_true)]
            ours = lab[lab.type.notna()]
            harmless = ours[ours.type.isin(RISKY_TYPES) & (ours.privacy_role == "non_sensitive")]
            other = lab[lab.type.isna()]
            row[m]["model_types"] = {"columns": len(ours), "role_correct": int((ours.privacy_role == ours.privacy_role_true).sum()),
                                     "harmless": len(harmless),
                                     "harmless_columns": [f"{r.column} ({r.subtype_true} -> {r.subtype})" for r in harmless.itertuples()]}
            row[m]["other_columns"] = {"columns": len(other),
                                       "role_correct": int((other.privacy_role == other.privacy_role_true).sum()),
                                       "wrong": [f"{r.column}: {r.privacy_role_true} {r.subtype_true} -> {r.privacy_role} {r.subtype}"
                                                 for r in other.itertuples() if r.privacy_role != r.privacy_role_true]}
        row["gate_harmless_at_most_1"] = row["hybrid"]["model_types"]["harmless"] <= 1
        body["countries"][loc] = row
        warn[loc] = warnings(reps["hybrid"])
        if model is not None:
            df = pd.concat([pd.read_csv(f, dtype=str) for f in sorted((folder / loc).glob("*.csv"))], axis=1)
            for r in cat.itertuples():
                t = model_type(r.privacy_role, r.subtype)
                p = model.predict_proba(sample_values(df[r.column])) if t and r.column in df else None
                if p is not None and t in model.types:
                    calib.append((np.array([p[x] for x in model.types]), model.types.index(t)))
        print(loc, {m: row[m]["macro_f1"] for m in MODES},
              f"harmless {row['hybrid']['model_types']['harmless']}, warnings {warn[loc]['needs_review']}")
    body["summary"] = {m: {loc: body["countries"][loc][m]["macro_f1"] for loc in body["countries"]} for m in MODES}
    body["gate_all_countries"] = all(c["gate_harmless_at_most_1"] for c in body["countries"].values())
    return body, warn, calib


def corpus_points(path: Path) -> list[tuple[np.ndarray, int]]:
    model = load_model()
    pts = []
    with path.open(encoding="utf-8") as f:
        f.readline()
        for line in f:
            r = json.loads(line)
            p = model.predict_proba(sample_values(pd.Series(r["values"], dtype=str)))
            if p is not None and r["type"] in model.types:
                pts.append((np.array([p[x] for x in model.types]), model.types.index(r["type"])))
    return pts


def calibration(sets: dict[str, list[tuple[np.ndarray, int]]]) -> dict:
    types = load_model().types
    out = {}
    for name, pts in {**sets, "all": [p for v in sets.values() for p in v]}.items():
        if not pts:
            continue
        P, y = np.stack([p for p, _ in pts]), np.array([t for _, t in pts])
        pred = P.argmax(axis=1)
        out[name] = {"columns": len(y), "accuracy": round(float((pred == y).mean()), 4), "ece": round(ece(P, y), 4),
                     "reliability": reliability(P, y),
                     "per_type_accuracy": {types[k]: round(float((pred[y == k] == k).mean()), 4)
                                           for k in range(len(types)) if (y == k).any()}}
    return out


def cost() -> dict:
    datasets = TUNING + HELD_OUT
    load_model.cache_clear()  # main() already loaded it; time a fresh load
    t = time.time()
    load_model()
    load = time.time() - t
    secs = {m: {} for m in MODES}
    for m in MODES:
        for d in datasets:
            t = time.time()
            run(PG / "data" / d, d, m)
            secs[m][d] = round(time.time() - t, 2)
    tot = {m: round(sum(secs[m].values()), 1) for m in MODES}
    return {"machine": "zray's laptop, 12 CPU threads, CPU-only torch", "model_load_seconds": round(load, 1),
            "seconds": secs, "total_seconds": tot, "ratio_hybrid_to_lexicon": round(tot["hybrid"] / tot["lexicon"], 2),
            "gate_at_most_3x": tot["hybrid"] <= 3 * tot["lexicon"]}


def advisor() -> dict:
    """Advisor mode (added after the test run, SPLIT.md): labels must equal lexicon's; each review flag is checked
    against the answer key. A "catch" flags a column whose word-list role is wrong; a "false alarm" one whose role is
    right. "missed" counts wrong word-list roles that got no flag. The unseen export has no answer key."""
    pg = pd.read_csv(PG / "metadata" / "field_catalog.csv", dtype=str)
    sets = [(PG / "data" / d, d, pg, "proving_ground_" + ("tuning" if d in TUNING else "held_out"))
            for d in TUNING + HELD_OUT]
    for split in ("dev", "locked"):
        cat = pd.read_csv(EVAL / split / "catalog.csv", dtype=str)
        sets += [(EVAL / split / loc, loc, cat, f"eu_{split}") for loc in sorted(cat.dataset.unique())]
    sets.append((PG / "data" / "unseen", "unseen", None, "unseen"))
    body, totals = {"datasets": {}}, {}
    for folder, name, catalog, group in sets:
        lex, adv = run(folder, name, "lexicon"), run(folder, name, "advisor")
        truth = {} if catalog is None else {(r.table, r.column): r.privacy_role
                                            for r in catalog[catalog.dataset == name].itertuples()}
        word = {(r.table, r.column): r.privacy_role for r in lex.labels.itertuples()}
        flags = []
        for r in adv.needs_review.itertuples():
            k = (r.table, r.column)
            verdict = None if k not in truth else ("catch" if word[k] != truth[k] else "false alarm")
            suggestion = r.reason.split("; model suggests ")[1] if "; model suggests " in r.reason else None
            flags.append({"table": r.table, "column": r.column, "flag": r.flag, "word_lists": word[k],
                          "model_suggests": suggestion, "truth": truth.get(k), "verdict": verdict})
        flagged = {(f["table"], f["column"]) for f in flags}
        wrong = [k for k in truth if k in word and word[k] != truth[k]]
        row = {"group": group, "labels_equal_lexicon": bool(lex.labels.equals(adv.labels)), "columns": len(word),
               "flags": flags, "catches": sum(f["verdict"] == "catch" for f in flags),
               "false_alarms": sum(f["verdict"] == "false alarm" for f in flags),
               "word_list_wrong": len(wrong), "missed": sum(k not in flagged for k in wrong)}
        body["datasets"][name] = row
        tot = totals.setdefault(group, dict.fromkeys(("columns", "flags", "catches", "false_alarms",
                                                      "word_list_wrong", "missed"), 0))
        for key in list(tot):
            if key != "by_flag":
                tot[key] += len(row["flags"]) if key == "flags" else row[key]
        for f in flags:
            bf = tot.setdefault("by_flag", {}).setdefault(f["flag"], {"flags": 0, "catches": 0, "false_alarms": 0})
            bf["flags"] += 1
            bf["catches"] += f["verdict"] == "catch"
            bf["false_alarms"] += f["verdict"] == "false alarm"
        print(name, f"flags {len(flags)}, catches {row['catches']}, false alarms {row['false_alarms']}, "
                    f"missed {row['missed']} of {len(wrong)} wrong, labels equal {row['labels_equal_lexicon']}")
    body["totals"] = totals
    body["all_labels_equal_lexicon"] = all(r["labels_equal_lexicon"] for r in body["datasets"].values())
    return body


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--split", choices=["dev", "test"])
    g.add_argument("--cost", action="store_true")
    g.add_argument("--advisor", action="store_true", help="advisor mode: flags against the answer key")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "detect-semantic")
    a = ap.parse_args(argv)
    if load_model() is None:
        sys.exit("the model is not installed: see scripts/semantic/TRAINING.md")
    a.out.mkdir(parents=True, exist_ok=True)
    st = stamp()
    if a.cost:
        write(a.out, "e5_cost.json", cost(), st)
        return
    if a.advisor:
        write(a.out, "advisor.json", advisor(), st)
        return
    if a.split == "test" and (a.out / "e1_proving_ground_test.json").exists():
        sys.exit("the test split has already been run once (SPLIT.md); not running it again")
    st["split"] = a.split
    datasets = TUNING if a.split == "dev" else HELD_OUT
    tables = EVAL / ("dev" if a.split == "dev" else "locked")
    corpus = CORPUS / ("calib.jsonl" if a.split == "dev" else "locked.jsonl")

    body1, warn1 = e1(datasets)
    write(a.out, f"e1_proving_ground_{a.split}.json", body1, st)
    body2, warn2, table_pts = e2(tables)
    write(a.out, f"e2_eu_{a.split}.json", body2, st)
    if a.split == "dev":
        reps = {m: run(PG / "data" / "unseen", "unseen", m) for m in MODES}
        write(a.out, "e2b_unseen.json", {"columns": len(reps["hybrid"].labels),
              "changed": changed(reps["lexicon"].labels, reps["hybrid"].labels, reps["hybrid"].type_probs),
              "warnings": warnings(reps["hybrid"])}, st)
    write(a.out, f"e3_calibration_{a.split}.json",
          {"sets": calibration({corpus.stem: corpus_points(corpus), f"{tables.name}_tables": table_pts})}, st)
    pg_total = sum(w["columns"] for w in warn1.values())
    pg_flag = sum(w["needs_review"] for w in warn1.values())
    write(a.out, f"e4_warnings_{a.split}.json",
          {"proving_ground": warn1, "eu_tables": warn2,
           "proving_ground_total": {"columns": pg_total, "needs_review": pg_flag,
                                    "share": round(pg_flag / pg_total, 4) if pg_total else 0.0}}, st)


if __name__ == "__main__":
    main()
