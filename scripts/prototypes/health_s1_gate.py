"""Protect step only; scoring is done by the pets-eval CLI.
Prototype gate for HEALTH-S1: does keeping only time of day in arrival_ts give H-U8 > 0 with a low k<5 share?

Usage: python health_s1_gate.py hour|hour_weekday|q15   (writes protected tables to out/)
"""
import hashlib
import hmac
import os
import sys
from pathlib import Path

import pandas as pd
from pets_eval import parse

REPO = Path("/Users/ardasarikaya/Desktop/Business/team-1-trusted")
PG = REPO / "data" / "proving-ground"
SRC = PG / "data" / "health"
OUT = REPO / "out" / "health-s1-gate" / "health"
KEYFILE = REPO / "out" / "health-s1-gate" / "hmac.key"  # out/ is gitignored

OUT.mkdir(parents=True, exist_ok=True)
if not KEYFILE.exists():
    KEYFILE.write_bytes(os.urandom(32))
key = KEYFILE.read_bytes()

v = pd.read_csv(SRC / "ed_visits.csv", dtype=str)
labs = pd.read_csv(SRC / "lab_results.csv", dtype=str)

p = v.drop(columns=["patient_name", "phone", "home_address", "postcode", "ambulance_unit", "chief_complaint",
                    "discharge_ts", "attending_physician_id", "attending_physician_name"]).copy()
# "P" prefix: a bare hex pseudonym starting 04... matched the pets-eval PHONE pattern; "P-" would not help because \b0 matches after "-"
p["patient_hetu"] = v.patient_hetu.map(lambda x: "P" + hmac.new(key, str(x).encode(), hashlib.sha256).hexdigest()[:16])
# the scorer counts k only over catalogued quasi-identifier columns; the catalogue lists date_of_birth, not age
# H-U6 reads a column named age, so the same band is kept there too
p["date_of_birth"] = parse.to_age_band(parse.age_from_birth(v.date_of_birth))
p["age"] = p["date_of_birth"]
top8 = v.municipality[v.municipality != "non-resident"].value_counts().index[:8]
p["municipality"] = v.municipality.where(v.municipality.isin(top8), "other")
t = parse.to_datetime(v.arrival_ts)
mode = sys.argv[1]
if mode == "q15":
    p["arrival_ts"] = t.dt.floor("15min").dt.strftime("%H:%M")
else:
    p["arrival_ts"] = t.dt.strftime("%H:00")
if mode == "hour_weekday":
    p["arrival_weekday"] = t.dt.day_name()
p.to_csv(OUT / "ed_visits.csv", index=False)
pd.DataFrame({"protected_row": range(len(p)), "original_record_id": v.visit_id}).to_csv(OUT / "rowmap_ed_visits.csv", index=False)

l = labs.drop(columns=["sampled_ts"])
l.to_csv(OUT / "lab_results.csv", index=False)
pd.DataFrame({"protected_row": range(len(l)), "original_record_id": labs.lab_id}).to_csv(OUT / "rowmap_lab_results.csv", index=False)

# clinical_notes and published_weekly_stats are withheld: not written
for f in ("clinical_notes.csv", "published_weekly_stats.csv"):
    (OUT / f).unlink(missing_ok=True)
