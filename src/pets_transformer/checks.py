"""Three checks the organisers' scorecard does not run: l-diversity, an informed attacker, k on the joined tables.

Every JSON holds counts and rates only: never truth values, row-map contents or the values of a group.
"""
import json
from pathlib import Path

import pandas as pd
from pets_eval.utility.health import diagnosis_group

from . import pets
from .score import ROOT, rewrite_paths

# The scorer's k columns on ed_visits (catalogued quasi-identifiers that survive protection).
QIS = ["date_of_birth", "sex", "municipality", "arrival_ts", "arrival_mode"]
SENSITIVE = "icd10_primary"
FACTS = ["diagnosis_group", "age_band", "municipality", "arrival_hour"]
EXACT = ["icd10_primary", "date_of_birth", "municipality", "arrival_ts"]


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


def attacker_facts(df, municipalities=None):
    """The informed attacker's four facts, from original values; a municipality the release does not show becomes "other"."""
    m = df["municipality"].fillna("")
    if municipalities is not None:
        m = m.where(m.isin(municipalities), "other")
    return pd.DataFrame({"diagnosis_group": diagnosis_group(df["icd10_primary"]).fillna("").values,
                         "age_band": pets.age_band(df["date_of_birth"]).fillna("").values,
                         "municipality": m.values, "arrival_hour": pets.hour_of_day(df["arrival_ts"]).fillna("").values})


def release_facts(df):
    """The same four facts read from the protected release, which already holds bands and hours."""
    return pd.DataFrame({"diagnosis_group": diagnosis_group(df["icd10_primary"]).fillna("").values,
                         "age_band": df["date_of_birth"].fillna("").values,
                         "municipality": df["municipality"].fillna("").values, "arrival_hour": df["arrival_ts"].fillna("").values})


def singled_out(attacker, released, released_records, cols):
    """attacker: frame of cols plus record_id. released: frame of cols, one row per released row; released_records:
    the original record id of each released row (the row map). Singled out = exactly one released row matches."""
    key = lambda f: pd.util.hash_pandas_object(f[cols].astype(str), index=False)  # noqa: E731
    rk = key(released)
    counts = rk.value_counts()
    only = pd.Series(list(released_records), index=rk.values)[rk.map(counts).eq(1).values]
    ak = key(attacker)
    single = ak.map(counts).eq(1)
    correct = single & ak.map(only).astype(object).eq(attacker["record_id"].values).values
    n = len(attacker)
    return {"n_attacker_rows": int(n), "n_singled_out": int(single.sum()), "n_correct": int(correct.sum()),
            "singled_out_rate": round(float(single.mean()), 4) if n else 0.0,
            "correct_among_singled_out": round(float(correct.sum() / single.sum()), 4) if single.sum() else None,
            "correct_rate": round(float(correct.mean()), 4) if n else 0.0}


def informed_attacker(original_ed, protected_ed, rowmap, truth_ids=None):
    orig = original_ed if truth_ids is None else original_ed[original_ed["visit_id"].isin(set(truth_ids))]
    att = attacker_facts(orig).assign(record_id=orig["visit_id"].values)
    att_p = attacker_facts(orig, set(protected_ed["municipality"].fillna(""))).assign(record_id=orig["visit_id"].values)
    recs = rowmap.set_index("protected_row")["original_record_id"].reindex(range(len(protected_ed))).values
    exact = orig[EXACT].fillna("").assign(record_id=orig["visit_id"].values)
    return {"protected": singled_out(att_p, release_facts(protected_ed), recs, FACTS),
            "original_same_facts": singled_out(att, attacker_facts(original_ed), original_ed["visit_id"].values, FACTS),
            "original_exact_values": singled_out(exact, original_ed[EXACT].fillna(""), original_ed["visit_id"].values, EXACT)}


def catalogue_columns(catalog, dataset, tables):
    c = catalog[(catalog.dataset == dataset) & catalog.table.isin(tables)]
    return sorted(set(c[(c.privacy_role == "quasi_identifier") | (c.subtype == "DIAGNOSIS_CODE")].column))


def joined_k(ed, lab, cols):
    j = ed.merge(lab, on="visit_id", how="inner")
    cols = [c for c in cols if c in j.columns and c != "visit_id"]
    d = j[cols + ["visit_id"]].fillna("")
    visits = d.groupby(cols)["visit_id"].transform("nunique")
    rows = d.groupby(cols)["visit_id"].transform("size")
    return {"join": "ed_visits inner join lab_results on visit_id", "columns": cols, "n_joined_rows": int(len(d)),
            "n_visits": int(d.visit_id.nunique()), "n_groups": int(d.groupby(cols).ngroups),
            "k_unit": "distinct visits per group (one visit has several lab rows, so rows would overstate k)",
            "share_rows_k_below_5": round(float((visits < 5).mean()), 4),
            "share_visits_k_below_5": round(float(d.assign(v=visits).groupby("visit_id").v.first().lt(5).mean()), 4),
            "share_rows_k_below_5_counting_rows": round(float((rows < 5).mean()), 4),
            "min_k": int(visits.min())}


def run(protected, original, out, truth=None, argv=None):
    protected, original, out = Path(protected), Path(original), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    ped, ped_orig = _read(protected / "ed_visits.csv"), _read(original / "ed_visits.csv")
    command = "python -m pets_transformer.cli " + " ".join(argv or [])
    prefixes = [ROOT, original.absolute().parents[2], original.resolve().parents[2], Path.home()]
    base = {"command": command, "protected": str(protected), "original": str(original)}

    ld = l_diversity(ped)
    fix_cols = [q for q in QIS if q != "arrival_mode"]
    ld_fix = l_diversity(ped, fix_cols) if "arrival_mode" in ped.columns else None
    triggered = ld["share_groups_l_below_2"] > 0.05
    l_out = {**base, "check": "l-diversity of icd10_primary within groups sharing the scorer's quasi-identifier values",
             "threshold": "a finding when more than 5% of groups have fewer than 2 distinct diagnoses",
             "finding": triggered, "result": ld}
    if triggered and ld_fix:
        l_out["proposed_fix"] = {"change": "drop arrival_mode from ed_visits (named column rule in contracts/HEALTH-S1.json)",
                                 "why": "no HEALTH-S1 task reads it; 20-year bands or wider hour blocks break H-U6 and H-U8 (results/sweep/sweep.md)",
                                 "result_after": ld_fix}

    rowmap = _read(protected / "rowmap_ed_visits.csv")
    rowmap["protected_row"] = rowmap["protected_row"].astype(int)
    truth_ids = _read(Path(truth) / "health__ed_visits.csv")["record_id"] if truth else None
    ia = informed_attacker(ped_orig, ped, rowmap, truth_ids)
    ia_out = {**base, "truth": str(truth) if truth else None,
              "check": "informed attacker: knows four facts about every visit and looks for a unique match",
              "attacker_knows": {"diagnosis_group": "group of icd10_primary as pets_eval.utility.health.diagnosis_group defines it",
                                 "age_band": "10-year band of date_of_birth (the release's own method)",
                                 "municipality": "home municipality, mapped to other when the release does not show it",
                                 "arrival_hour": "hour of arrival_ts"},
              "attacker_rows": "every visit listed in truth/health__ed_visits.csv" if truth else "every visit in the original ed_visits",
              "singled_out": "exactly one released row has the attacker's facts",
              "correct": "the row map of that row points at the attacker's visit",
              "original_exact_values": "same attacker on the original with exact icd10_primary, date_of_birth, municipality and arrival_ts",
              "result": ia}

    catalog = _read(original.parents[1] / "metadata" / "field_catalog.csv")
    cols = catalogue_columns(catalog, original.name, ["ed_visits", "lab_results"])
    lab = _read(protected / "lab_results.csv")
    jk_out = {**base, "check": "k over the ed_visits-lab_results join",
              "column_rule": "retained columns of the join that metadata/field_catalog.csv marks quasi_identifier or DIAGNOSIS_CODE",
              "result": joined_k(ped, lab, cols),
              "for_comparison_without_diagnoses": joined_k(ped, lab, [c for c in cols if c in QIS])}

    for name, obj in (("l_diversity.json", l_out), ("informed_attacker.json", ia_out), ("joined_k.json", jk_out)):
        (out / name).write_text(rewrite_paths(json.dumps(obj, indent=2), prefixes) + "\n")
    return l_out, ia_out, jk_out
