"""Three checks the organisers' scorecard does not run: l-diversity, an informed attacker, k on the joined tables.

They read the contract's k target (table, k columns, sensitive column, join flags), so they run on any dataset whose
contract has one. Every JSON holds counts and rates only: never truth values, row-map contents or the values of a group.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from pets_eval.utility.health import diagnosis_group

from . import protect
from .generalise import covers
from .score import ROOT, rewrite_paths

# Defaults for the health ED tables (the unit tests and the old command line use them).
QIS = ["date_of_birth", "sex", "municipality", "arrival_ts", "arrival_mode"]
SENSITIVE = "icd10_primary"
ICD = r"[A-Z]\d\d"


def _read(p):
    return pd.read_csv(p, dtype=str)


def l_diversity(df, qis=QIS, sensitive=SENSITIVE):
    qis = [q for q in qis if q in df.columns]
    d = df[qis + [sensitive]].fillna("")
    g = d.groupby(qis)[sensitive]
    distinct, size = g.nunique(), g.size()
    worst = pd.DataFrame({"distinct": distinct, "size": size}).sort_values(["distinct", "size"], ascending=[True, False]).iloc[0]
    rec = d.groupby(qis)[sensitive].transform("nunique")
    return {"columns": qis, "sensitive": sensitive, "n_rows": int(len(d)), "n_groups": int(len(size)),
            "share_groups_l_below_2": round(float((distinct < 2).mean()), 4),
            "share_groups_l_below_3": round(float((distinct < 3).mean()), 4),
            "share_records_l_below_2": round(float((rec < 2).mean()), 4),
            "share_records_l_below_3": round(float((rec < 3).mean()), 4),
            "worst_group": {"rule": "fewest distinct diagnoses, then largest size", "size": int(worst["size"]), "distinct": int(worst["distinct"])}}


def singled_out(attacker, released, released_records, cols):
    """Exact matching (no generalised values). attacker: frame of cols plus record_id. released: frame of cols, one
    row per released row; released_records: the original record id of each released row (the row map).
    Singled out = exactly one released row matches."""
    key = lambda f: pd.util.hash_pandas_object(f[cols].astype(str), index=False)  # noqa: E731
    rk = key(released)
    counts = rk.value_counts()
    only = pd.Series(list(released_records), index=rk.values)[rk.map(counts).eq(1).values]
    ak = key(attacker)
    single = ak.map(counts).eq(1)
    correct = single & ak.map(only).astype(object).eq(attacker["record_id"].values).values
    return _rates(len(attacker), int(single.sum()), int(correct.sum()))


def _rates(n, single, correct):
    return {"n_attacker_rows": int(n), "n_singled_out": single, "n_correct": correct,
            "singled_out_rate": round(single / n, 4) if n else 0.0,
            "correct_among_singled_out": round(correct / single, 4) if single else None,
            "correct_rate": round(correct / n, 4) if n else 0.0}


def singled_out_covering(attacker, released, released_records, cols, ops=None):
    """Like singled_out, but a released row matches an attacker row when each of its values can stand for the
    attacker's value (generalise.covers: a wider band, an hour block, "other", suppressed...). ops maps a column to
    the repair ladder steps that may have touched it."""
    ops = ops or {}
    cols = list(cols)
    att = attacker[cols].fillna("").astype(str)
    rel = released[cols].fillna("").astype(str).reset_index(drop=True)
    # code every attacker value per column; a released value becomes the boolean set of attacker codes it covers
    codes, cover = [], []
    for c in cols:
        vals = pd.Index(att[c].unique())
        codes.append(vals.get_indexer(att[c]))
        cover.append({rv: np.array([covers(rv, bv, ops.get(c, ())) for bv in vals]) for rv in rel[c].unique()})
    A = np.stack(codes, axis=1) if cols else np.zeros((len(att), 0), dtype=int)
    tup, inv = np.unique(A, axis=0, return_inverse=True)
    inv = inv.ravel()
    count = np.zeros(len(tup), dtype=np.int64)
    last = np.full(len(tup), -1, dtype=np.int64)
    rel_groups = rel.groupby(cols, sort=False).indices
    for vals, rows in rel_groups.items():
        vals = vals if isinstance(vals, tuple) else (vals,)
        m = np.ones(len(tup), dtype=bool)
        for j, (c, v) in enumerate(zip(cols, vals)):
            m &= cover[j][v][tup[:, j]]
        count[m] += len(rows)
        last[m] = rows[0]
    recs = np.asarray(list(released_records), dtype=object)
    single = count[inv] == 1
    hit = last[inv]
    correct = single & (recs[np.where(hit >= 0, hit, 0)] == attacker["record_id"].astype(str).values)
    return _rates(len(att), int(single.sum()), int(correct.sum()))


def catalogue_columns(catalog, dataset, tables):
    c = catalog[(catalog.dataset == dataset) & catalog.table.isin(tables)]
    return sorted(set(c[(c.privacy_role == "quasi_identifier") | (c.subtype == "DIAGNOSIS_CODE")].column))


def joined_k(ed, lab, cols, on="visit_id"):
    j = ed.merge(lab, on=on, how="inner")
    cols = [c for c in cols if c in j.columns and c != on]
    d = j[cols + [on]].fillna("")
    visits = d.groupby(cols)[on].transform("nunique")
    rows = d.groupby(cols)[on].transform("size")
    return {"join": f"inner join on {on}", "columns": cols, "n_joined_rows": int(len(d)),
            "n_visits": int(d[on].nunique()), "n_groups": int(d.groupby(cols).ngroups),
            "k_unit": "distinct main-table records per group (one record has several joined rows, so rows would overstate k)",
            "share_rows_k_below_5": round(float((visits < 5).mean()), 4),
            "share_visits_k_below_5": round(float(d.assign(v=visits).groupby(on).v.first().lt(5).mean()), 4),
            "share_rows_k_below_5_counting_rows": round(float((rows < 5).mean()), 4),
            "min_k": int(visits.min())}


def sensitive_fact(s):
    """What the informed attacker knows of the sensitive value: the diagnosis group for ICD-10 codes, else the value."""
    s = s.fillna("")
    if s.str.match(ICD).mean() > 0.9:
        return diagnosis_group(s).fillna("").astype(str), "group of the code as pets_eval.utility.health.diagnosis_group defines it"
    return s.astype(str), "the exact value"


def informed_attacker(contract, orig, rel, rowmap, truth_ids=None, key=b"k" * 32):
    """The attacker knows, for every record, the k columns at the release's own base precision (the column rule
    applied to the true value: an attacker learns a 10-year band and an hour as easily as the release shows them)
    and the sensitive fact. A released row matches when its values cover the attacker's."""
    kt = contract["k_target"]
    main, cols, sens = kt["table"], kt["columns"], kt.get("sensitive")
    rid = contract["tables"][main]["record_id"]
    base = pd.DataFrame({c: protect.column_values(orig[c], contract["columns"][main][c], key).values for c in cols})
    released = rel[cols].copy()
    facts = list(cols)
    knows = {c: f"{contract['columns'][main][c]['pet']} of the true value" for c in cols}
    if sens:
        base["_sensitive"], how = sensitive_fact(orig[sens])
        released["_sensitive"], _ = sensitive_fact(rel[sens])
        facts.append("_sensitive")
        knows[sens] = how
    base["record_id"] = orig[rid].astype(str).values
    att = base if truth_ids is None else base[base.record_id.isin(set(truth_ids))]
    ops = {}
    for step in kt["ladder"].values():
        ops.setdefault(step["column"], []).append(step)
    recs = rowmap.set_index("protected_row")["original_record_id"].reindex(range(len(rel))).astype(str).values
    return knows, {"protected": singled_out(att, released, recs, facts),
                   "protected_counting_generalised_rows": singled_out_covering(att, released, recs, facts, ops),
                   "original_same_facts": singled_out(att, base, base.record_id.values, facts)}


def run(protected, original, out, truth=None, argv=None, contract=None):
    protected, original, out = Path(protected), Path(original), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    kt = (contract or {}).get("k_target")
    if not kt:
        raise KeyError("the contract has no k_target: nothing to check l-diversity, an informed attacker or joined k against")
    main, cols, sens = kt["table"], kt["columns"], kt.get("sensitive")
    rel, orig = _read(protected / f"{main}.csv"), _read(original / f"{main}.csv")
    command = "python -m pets_transformer.cli " + " ".join(argv or [])
    prefixes = [ROOT, original.absolute().parents[2], original.resolve().parents[2], Path.home()]
    base = {"command": command, "protected": str(protected), "original": str(original), "table": main}
    written = {}

    if sens:
        ld = l_diversity(rel, cols, sens)
        written["l_diversity.json"] = {**base, "check": f"l-diversity of {sens} within groups sharing the k columns of the release",
                                       "threshold": f"l of at least {kt.get('l', 1)} in every group (the repair's target)",
                                       "finding": ld["share_groups_l_below_2"] > 0, "result": ld}

    rowmap = _read(protected / f"rowmap_{main}.csv")
    rowmap["protected_row"] = rowmap["protected_row"].astype(int)
    tfile = Path(truth) / f"{original.name}__{main}.csv" if truth else None
    truth_ids = _read(tfile)["record_id"] if tfile and tfile.exists() else None
    knows, ia = informed_attacker(contract, orig, rel, rowmap, truth_ids)
    written["informed_attacker.json"] = {
        **base, "truth": str(truth) if truth_ids is not None else None,
        "check": "informed attacker: knows the k columns and the sensitive fact of every record and looks for a unique match",
        "attacker_knows": knows,
        "attacker_rows": f"every record listed in truth/{original.name}__{main}.csv" if truth_ids is not None else f"every record in the original {main}",
        "singled_out": "exactly one released row shows exactly the attacker's facts; rows the repair coarsened are taken to be someone else (the attacker's best case, our headline)",
        "protected_counting_generalised_rows": "same, but a coarsened row also matches when it can stand for the attacker's facts (a wider band, an hour block, other or suppressed); lower, because the 60-odd suppressed rows can stand for almost anyone",
        "correct": "the row map of that row points at the attacker's record",
        "original_same_facts": "same attacker against the original at the same precision, before the repair",
        "result": ia}

    # every released table that carries the main table's record key joins to it (join flag or not)
    rid = contract["tables"][main]["record_id"]
    flags = kt.get("join_flags") or [
        {"table": t, "on": rid} for t, s in contract["tables"].items()
        if t != main and s["action"] == "release" and (protected / f"{t}.csv").exists()
        and rid in pd.read_csv(protected / f"{t}.csv", nrows=0).columns and rid in rel.columns]
    if flags:
        catalog = _read(original.parents[1] / "metadata" / "field_catalog.csv")
        res = {}
        for jf in flags:
            other = _read(protected / f"{jf['table']}.csv")
            jcols = catalogue_columns(catalog, original.name, [main, jf["table"]])
            res[jf["table"]] = {"result": joined_k(rel, other, jcols, jf["on"]),
                                "for_comparison_k_columns_only": joined_k(rel, other, cols, jf["on"])}
        first = next(iter(res.values()))
        written["joined_k.json"] = {**base, "check": f"k over the join of {main} with " + ", ".join(res),
                                    "column_rule": "retained columns of the join that metadata/field_catalog.csv marks quasi_identifier or DIAGNOSIS_CODE",
                                    "result": first["result"], "for_comparison_k_columns_only": first["for_comparison_k_columns_only"],
                                    "per_join": res}

    for name, obj in written.items():
        (out / name).write_text(rewrite_paths(json.dumps(obj, indent=2), prefixes) + "\n")
    return written
