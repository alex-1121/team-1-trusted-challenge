"""Red team: attacks the organisers' scorecard does not run, each with a pass/fail threshold (the release gate).

1. Order attack. The release keeps the hour of arrival only. If the rows can be put back in arrival order (file order,
   a sequential record key, a sequential key in a linked table), a new day starts wherever the hour goes backwards,
   and the dropped date comes back. Measured: share of released rows whose date is rebuilt exactly.
2. News-clip linkage. The shipped news clips name a date, a clock hour, a place, an age and a sex. Matched against the
   release with the dates from the best ordering. Measured: share of clips that single out the right patient.
3. Person fingerprint. A pseudonym column links every row of a person; age band, sex, municipality and the set of
   arrival hours then form a fingerprint. Measured: share of released persons whose fingerprint is unique.

JSON output holds counts and rates only: never truth values, row-map contents or the values of a group.
"""
import json
import re
from pathlib import Path

import pandas as pd

GATE = {"order_attack": 0.05, "news_linkage": 0.0, "person_fingerprint": 0.05}
HOUR = re.compile(r"^\d\d:00$")


def _read(p):
    return pd.read_csv(p, dtype=str)


def _time_column(contract):
    for t, cols in contract["columns"].items():
        for c, rule in cols.items():
            if rule["pet"] == "hour_of_day":
                return t, c
    raise ValueError("contract has no hour_of_day column, nothing for the order attack to rebuild")


def rebuild_days(hours):
    """hours in release order -> day index per row; a new day starts when the hour goes backwards."""
    h = pd.to_numeric(hours.where(hours.str.match(HOUR, na=False)).str[:2], errors="coerce").ffill().fillna(0)
    return (h.diff().fillna(0) < 0).cumsum()


def date_hit_rate(days, true_days):
    """Share of rows whose rebuilt day equals the true day, after the single best offset (the attacker needs one anchor)."""
    diff = (true_days.values - days.values)
    if not len(diff):
        return 0.0, 0
    offset = int(pd.Series(diff).mode().iloc[0])
    return float((diff == offset).mean()), offset


def orderings(rel, main, join_tables):
    """Candidate orders an attacker can try: file order, each unique column, first row per key in a linked table."""
    yield "file order", rel.index.to_numpy()
    for c in rel.columns:
        v = rel[c]
        if v.notna().all() and v.nunique() == len(v):
            yield f"sorted by {main}.{c}", v.sort_values(kind="stable").index.to_numpy()
    for t, other in join_tables.items():
        for jc in [c for c in other.columns if c in rel.columns and rel[c].nunique() == len(rel)]:
            pos = pd.Series(rel.index, index=rel[jc])
            for c in other.columns:
                v = other[c]
                if c == jc or not (v.notna().all() and v.nunique() == len(v)):
                    continue
                first = other.sort_values(c, kind="stable").drop_duplicates(jc)[jc]
                idx = pos.reindex(first.values).dropna().astype(int).to_numpy()
                yield f"first {t}.{c} per {jc}", idx


def order_attack(rel, orig_dates, main, time_col, join_tables):
    """orig_dates: true calendar date per released row (from the row map), aligned with rel."""
    t0 = pd.to_datetime(orig_dates).min()
    true_days = (pd.to_datetime(orig_dates) - t0).dt.days
    tried = []
    best = None
    for name, idx in orderings(rel, main, join_tables):
        if len(idx) < 2:
            continue
        days = rebuild_days(rel[time_col].iloc[idx].reset_index(drop=True))
        rate, offset = date_hit_rate(days, true_days.iloc[idx].reset_index(drop=True))
        tried.append({"ordering": name, "rows": int(len(idx)), "share_dates_rebuilt": round(rate, 4)})
        if best is None or rate * len(idx) > best[1] * len(best[2]):
            best = (name, rate, idx, days, offset)
    name, rate, idx, days, offset = best
    rebuilt = pd.Series(pd.NaT, index=rel.index, dtype="datetime64[ns]")
    rebuilt.iloc[idx] = (t0 + pd.to_timedelta(days.values + offset, unit="D")).values
    share_all = float((rebuilt.dt.normalize() == pd.to_datetime(orig_dates).dt.normalize()).mean())
    return {"orderings_tried": tried, "best_ordering": name, "share_rows_date_rebuilt": round(share_all, 4)}, rebuilt


def _age_ok(band, age):
    if not isinstance(band, str):
        return False
    if band.endswith("+"):
        return age >= int(band[:-1])
    m = re.fullmatch(r"(\d+)-(\d+)", band)
    return bool(m) and int(m.group(1)) <= age <= int(m.group(2))


def news_linkage(rel, rebuilt, rec_ids, news, truth_news, truth_rec, time_col, age_col="date_of_birth"):
    rel = rel.assign(_date=rebuilt.dt.strftime("%Y-%m-%d").values, _rec=rec_ids)
    t_news = truth_news.set_index("adv_row_id")["person_id"]
    t_rec = truth_rec.set_index("record_id")["person_id"]
    usable = singled = correct = 0
    for _, n in news.iterrows():
        m = re.search(r"kello (\d{1,2})", str(n.get("text", "")))
        if not m or not isinstance(n.get("event_date"), str):
            continue
        usable += 1
        c = rel[(rel._date == n.event_date) & (rel[time_col] == f"{int(m.group(1)):02d}:00")]
        if isinstance(n.get("sex_mentioned"), str) and "sex" in c:
            c = c[c.sex == n.sex_mentioned]
        if isinstance(n.get("place"), str) and "municipality" in c:
            c = c[c.municipality.isin([n.place, "other"])]
        if isinstance(n.get("age_mentioned"), str) and age_col in c:
            a = int(n.age_mentioned)
            c = c[c[age_col].map(lambda b: _age_ok(b, a))]
        if len(c) == 1:
            singled += 1
            correct += int(t_rec.get(c._rec.iloc[0]) == t_news.get(n.adv_row_id))
    return {"clips": int(len(news)), "clips_with_date_and_hour": usable, "singled_out": singled, "correct": correct,
            "share_clips_reidentified": round(correct / len(news), 4) if len(news) else 0.0}


def person_fingerprint(rel, person_cols, fp_cols, time_col):
    if not person_cols:
        return {"applicable": False, "why": "no person key released (no pseudonym column)", "share_persons_unique": 0.0}
    pc = person_cols[0]
    rel = rel[rel[pc].notna()]  # rows without a person key link to nobody
    d = rel[[pc] + [c for c in fp_cols if c in rel.columns and c != time_col]].fillna("")
    hours = rel.groupby(pc)[time_col].apply(lambda s: tuple(sorted(s.fillna(""))))
    static = d.groupby(pc).first()
    sig = static.apply(tuple, axis=1).astype(str) + "|" + hours.astype(str)
    counts = sig.map(sig.value_counts())
    visits = rel.groupby(pc).size()
    return {"applicable": True, "person_column": pc, "fingerprint": [c for c in fp_cols if c in rel.columns],
            "persons": int(len(sig)), "persons_with_2plus_rows": int((visits > 1).sum()),
            "share_persons_unique": round(float((counts == 1).mean()), 4),
            "share_repeat_persons_unique": round(float((counts[visits > 1] == 1).mean()), 4) if (visits > 1).any() else 0.0}


def run(protected, original, contract, out, truth=None, adversary=None, label=""):
    protected, original, out = Path(protected), Path(original), Path(out)
    main, time_col = _time_column(contract)
    rid = contract["tables"][main]["record_id"]
    rel = _read(protected / f"{main}.csv")
    rowmap = _read(protected / f"rowmap_{main}.csv")
    rec_ids = rowmap.set_index(rowmap.protected_row.astype(int))["original_record_id"].reindex(range(len(rel))).values
    orig = _read(original / f"{main}.csv").set_index(rid)
    orig_dates = pd.Series(orig[time_col].reindex(rec_ids).values).str[:10]
    joins = {f.stem: _read(f) for f in sorted(protected.glob("*.csv"))
             if f.stem != main and not f.stem.startswith("rowmap_") and f.stem != "plan"}
    oa, rebuilt = order_attack(rel, orig_dates, main, time_col, joins)

    news = None
    if adversary and truth and (Path(adversary) / "news_clips_health.csv").exists():
        news = news_linkage(rel, rebuilt, rec_ids, _read(Path(adversary) / "news_clips_health.csv"),
                            _read(Path(truth) / "adversary__news_clips_health.csv"),
                            _read(Path(truth) / f"{original.name}__{main}.csv"), time_col)
    person_cols = [c for c, r in contract["columns"].get(main, {}).items() if r["pet"] == "pseudonym" and c in rel.columns]
    fp_cols = (contract.get("k_target") or {}).get("columns") or ["date_of_birth", "sex", "municipality", time_col]
    pf = person_fingerprint(rel, person_cols, fp_cols, time_col)

    results = {
        "order_attack": {"metric": "share_rows_date_rebuilt", "value": oa["share_rows_date_rebuilt"], "detail": oa},
        "news_linkage": {"metric": "share_clips_reidentified", "value": news["share_clips_reidentified"] if news else None, "detail": news},
        "person_fingerprint": {"metric": "share_persons_unique", "value": pf["share_persons_unique"], "detail": pf},
    }
    for k, r in results.items():
        r["threshold"] = GATE[k]
        r["pass"] = None if r["value"] is None else bool(r["value"] <= GATE[k])
    passed = all(r["pass"] is not False for r in results.values())
    report = {"release": label or str(protected.name), "table": main, "time_column": time_col,
              "gate": "pass" if passed else "fail",
              "rule": "every attack at or below its threshold; thresholds are our choice, stated here",
              "attacks": results}
    out.mkdir(parents=True, exist_ok=True)
    return report


def write(report, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(report, indent=2) + "\n")
