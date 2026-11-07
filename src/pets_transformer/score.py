import json
import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PETS_EVAL = str(ROOT / ".venv" / "bin" / "pets-eval")
PROVING_GROUND = str(ROOT / "data" / "proving-ground")
K_COLUMNS = ["date_of_birth", "sex", "municipality", "arrival_ts"]
LABEL = "self-assessment, not the official judging score"

# Plain-words consequence per risk component; the value is the share the scorer measured.
MEANING = {
    "direct identifiers retained": "{v:.1%} of the checked values still look like a direct identifier, so a reader could name a person straight from the release.",
    "records with k<5": "{v:.1%} of the records share their quasi-identifier combination with fewer than 5 rows, so an attacker who knows those attributes about a person can narrow the match to a handful of rows or one.",
    "linkage re-identification": "{v:.1%} of the outside records tested could be matched to a row in the release, so an attacker holding public data could name patients.",
    "free-text identifier leakage": "{v:.1%} of the identifiers in free text were not removed, so a reader could still find names or numbers in the text.",
}


def rewrite_paths(text, prefixes):
    """Longest prefix first; a prefix followed by "/" is cut, a bare prefix becomes "~"."""
    for p in sorted({str(p).rstrip("/") for p in prefixes if p}, key=len, reverse=True):
        text = text.replace(p + "/", "").replace(p, "~")
    return text


def own_k(df, cols):
    size = df.groupby(cols, dropna=False)[cols[0]].transform("size")
    return float((size < 5).mean()), int(size.min())


def _f(x):
    return "not evaluated" if x is None else f"{x:.4f}"


def _row(cells):
    return "| " + " | ".join(cells) + " |"


def build_summary(card, baseline, k_own, k_cols, scenario):
    s, b = card["summary"], baseline and baseline["summary"]
    before_u = {u["id"]: u["score"] for u in baseline["utility"]} if baseline else {}
    out = [f"# {scenario} score summary", "", f"Every number is copied from scorecard.json or computed by `score`. {LABEL}.", "",
           "## Utility per task", "", _row(["Task", "What it measures", "Before", "After"]), _row(["---"] * 4)]
    for u in card["utility"]:
        out.append(_row([u["id"], u["description"], _f(before_u[u["id"]]) if u["id"] in before_u else "not run", _f(u["score"])]))
    out += ["", "## Privacy risk components (lower is better)", "", _row(["Component", "Before", "After"]), _row(["---"] * 3)]
    brc = baseline["risk_components"] if baseline else {}
    for name in dict.fromkeys([*brc, *card["risk_components"]]):
        out.append(_row([name, _f(brc[name]) if name in brc else "not run", _f(card["risk_components"][name]) if name in card["risk_components"] else "not released"]))
    out += ["", "## k-anonymity (smallest group of rows sharing the same attributes)", ""]
    for t, tab in card["tables"].items():
        k = tab.get("k_anonymity")
        if k and "qis" in k:
            out.append(f"- Scorer, {t}: columns {', '.join(k['qis'])}; k<5 share {k['share_below']['k<5']}; median k {k['median_k']}; min k {k['min_k']}.")
    share, mn = k_own
    out.append(f"- Our own, ed_visits: columns {', '.join(k_cols)}; k<5 share {share:.4f}; min k {mn}.")
    out += ["", "## Residual risk", ""]
    sentences = []
    for name, v in card["risk_components"].items():
        table, comp = name.split(": ", 1)
        if v is None:
            sentences.append(f"{table}, {comp}, was not evaluated by the scorer.")
        elif v > 0:
            sentences.append(f"{table}, {comp}, is {v}: " + MEANING.get(comp, "{v:.1%} of this risk remains.").format(v=v))
    out.append(" ".join(sentences) if sentences else "No risk component is above zero.")
    out.append("")
    out.append("Attacker model: the toolkit's shipped attackers only. Attacks run: linkage re-identification with the shipped attacker files, "
               "a dictionary attack on hashed columns, a direct-identifier pattern scan, and k over the quasi-identifiers in the field catalogue. "
               "Stronger attackers (more background knowledge, other outside data) were not tested.")
    out += ["", "## Scores", "", f"- Privacy {s['privacy']}, utility {s['utility']}, composite {s['composite']} ({s['label']})."]
    if b:
        out.append(f"- Before: privacy {b['privacy']}, utility {b['utility']}, composite {b['composite']}.")
    return "\n".join(out) + "\n"


def run(original, protected, scenario, out, baseline=None, contract=None, pets_eval=PETS_EVAL, proving_ground=PROVING_GROUND):
    original, protected, out = (Path(p).absolute() for p in (original, protected, out))
    out.mkdir(parents=True, exist_ok=True)
    pg = Path(proving_ground)
    sc = subprocess.run([pets_eval, "scorecard", "--original", str(original), "--protected", str(protected), "--scenario", scenario, "--out", str(out)], cwd=pg, capture_output=True, text=True)
    if sc.returncode:
        raise RuntimeError(f"pets-eval scorecard failed: {sc.stderr[-500:]}")
    ck = subprocess.run([pets_eval, "check", str(protected)], cwd=pg, capture_output=True, text=True)
    prefixes = [ROOT, pg.absolute().parents[1], pg.resolve().parents[1], Path.home()]
    texts = {"check.txt": ck.stdout + ck.stderr}
    for n in ("scorecard.json", "scorecard.html"):
        texts[n] = (out / n).read_text()
    card = json.loads(texts["scorecard.json"])
    base = json.loads(Path(baseline).read_text()) if baseline else None
    c = json.loads(Path(contract).read_text()) if contract else {}
    k_cols = c.get("k_columns") or K_COLUMNS
    main = (c.get("k_target") or {}).get("table", "ed_visits")
    k_own = own_k(pd.read_csv(protected / f"{main}.csv", dtype=str), k_cols)
    texts["summary.md"] = build_summary(card, base, k_own, k_cols, scenario)
    for n, t in texts.items():
        (out / n).write_text(rewrite_paths(t, prefixes) if n != "summary.md" else t)
    return card
