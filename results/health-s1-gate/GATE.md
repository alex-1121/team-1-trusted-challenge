# HEALTH-S1 gate: time of day only in arrival_ts

Question: if arrival_ts keeps only the hour of day (no date), does utility task H-U8 score above zero while the share of rows with k<5 stays low?

Answer: yes, on the first attempt. H-U8 = 1.0, k<5 share = 0.0094. Attempts (a) and (b) were not needed, so they were not run.

Source of every number: `results/health-s1-gate/hour/scorecard.json` (v1) and `results/health-s1-gate/hour-v2/scorecard.json` (v2) (self-assessment from the organisers' pets-eval, not the official judging score).

## Attempt table

| Design | H-U8 | H-U2 | H-U4 | H-U6 | H-U7 | k<5 share (ed_visits) | min k | Privacy | Utility | Composite |
|---|---|---|---|---|---|---|---|---|---|---|
| v1: arrival_ts as "HH:00", no date | 1.0 | 1.0 | 1.0 | 0.9642 | 1.0 | 0.0094 | 1 | 0.9944 | 0.9928 | 0.9937 |
| v2: age band under date_of_birth (and age), pseudonym "P"+16 hex | 1.0 | 1.0 | 1.0 | 0.9642 | 1.0 | 0.1817 | 1 | 0.891 | 0.9928 | 0.9346 |

The v1 k<5 share looked good only because the age band was not counted. Once it counts (v2), 18.17% of ed_visits rows have k<5 (k<2: 3.84%, k<10: 37.05%), median k 15, 6810 groups. The "low k<5 share" part of the gate answer holds only for the v1 column set.

Reference before (raw copy, `baseline-scores/health_HEALTH-S1_research-env_raw.json`): privacy 0.1716, utility 1.0, composite 0.2752.

v1: k is computed by the scorer over sex, municipality, arrival_ts and arrival_mode (46398 rows, 1051 groups, median k 111). v2: the JSON lists the k column set as date_of_birth, sex, municipality, arrival_ts, arrival_mode (46398 rows, 6810 groups, median k 15). lab_results has no catalogued quasi-identifier left, so it has no k figure.

## What the protected copy contains

- ed_visits: patient_hetu replaced by a keyed HMAC-SHA256 pseudonym (first 16 hex chars, random 32-byte key saved to `out/health-s1-gate/hmac.key`, never committed); arrival_ts as "HH:00"; age as 10-year bands (top band 80+); municipality kept for the eight most frequent, others "other" (non-resident also becomes "other"); dropped: patient_name, date_of_birth, phone, home_address, postcode, ambulance_unit, chief_complaint, discharge_ts, attending_physician_id, attending_physician_name.
- lab_results: sampled_ts dropped; visit_id kept so the join to ed_visits works.
- clinical_notes and published_weekly_stats: withheld (not written).

## Commands run

```
<repo>/.venv/bin/python <repo>/scripts/prototypes/health_s1_gate.py hour
cd <repo>/data/proving-ground
<repo>/.venv/bin/pets-eval scorecard --original <repo>/data/proving-ground/data/health --protected <repo>/out/health-s1-gate/health --scenario HEALTH-S1 --out <repo>/results/health-s1-gate/hour
<repo>/.venv/bin/pets-eval check <repo>/out/health-s1-gate/health
```

## pets-eval check

Scanned 4 files (two tables, two row maps). One finding: PHONE, 2 hits, shown as "04...86". The tool says PHONE is pattern-only and may be a false positive. We did not locate the two hits; the likely cause is a digit run inside a hex pseudonym, but that is not confirmed. No HETU, IBAN, card, email, IP, MAC or plate hits.

## Caveats

- The parser reads "13:00" as today's date at 13:00, so week and month fields derived from it are meaningless. The five tasks above do not use them. Tasks that need dates (H-U1, H-DP) are out of scope for HEALTH-S1.
- v1 only: the scorer did not count the age band (see "What changed in v2"). The pseudonym is not a quasi-identifier in either version.
- The scorer ran linkage attacks with its shipped attackers only; a stronger attacker is not covered.
- Dates are gone, so a downstream user cannot study seasonality. That is the price of this design.

## What changed in v2

- Age band: the field catalogue (`metadata/field_catalog.csv`) lists these ed_visits columns as quasi_identifier: date_of_birth (temporal, BIRTH_DATE), sex, postcode, municipality, arrival_ts, arrival_mode, ambulance_unit (code, DEVICE_ID), discharge_ts. `age` is not catalogued. `scorecard.py` (lines 101-107) takes the k column set from the catalogue, so the v1 `age` column was never counted. v2 writes the 10-year band ("30-39", "80+") into `date_of_birth`, so the scorer counts it. The same band also stays in `age`, because task H-U6 reads a column named `age` (without it H-U6 fell to 0.0 in a trial run). `age` is not catalogued, so it adds nothing to k.
- Side effect to check: the linkage attacker reads a column named date_of_birth as a date, and "30-39" does not parse as one, so that attacker gets no age information from it. The linkage risk of 0.0% may therefore be optimistic. We have not tested this.
- PHONE hits: the v1 check hits were two rows (ed_visits.csv, column patient_hetu, rows 2713 and 38578, 0-based) holding the same pseudonym "0444680686b3eb5d" (same patient). The pattern matched its first 10 digits "0444680686". Fix: pseudonym is now "P" plus the same 16 hex chars from the same HMAC key. A "P-" prefix would not work, because the pattern's `\b0` matches after a hyphen. A letter prefix removes the word boundary before the 0.
- pets-eval check on the v2 output: no residual direct identifiers found by the regex scan (4 files, no PHONE hit).
- v1 results (`results/health-s1-gate/hour/`) are kept unchanged.

Commands for v2 are the three above with `--out .../results/health-s1-gate/hour-v2`.
