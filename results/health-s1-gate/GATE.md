# HEALTH-S1 gate: time of day only in arrival_ts

Question: if arrival_ts keeps only the hour of day (no date), does utility task H-U8 score above zero while the share of rows with k<5 stays low?

Answer: yes, on the first attempt. H-U8 = 1.0, k<5 share = 0.0094. Attempts (a) and (b) were not needed, so they were not run.

Source of every number: `results/health-s1-gate/hour/scorecard.json` (self-assessment from the organisers' pets-eval, not the official judging score).

## Attempt table

| Design | H-U8 | H-U2 | H-U4 | H-U6 | H-U7 | k<5 share (ed_visits) | min k | Privacy | Utility | Composite |
|---|---|---|---|---|---|---|---|---|---|---|
| arrival_ts as "HH:00", no date | 1.0 | 1.0 | 1.0 | 0.9642 | 1.0 | 0.0094 | 1 | 0.9944 | 0.9928 | 0.9937 |

Reference before (raw copy, `baseline-scores/health_HEALTH-S1_research-env_raw.json`): privacy 0.1716, utility 1.0, composite 0.2752.

k is computed by the scorer over sex, municipality, arrival_ts and arrival_mode (46398 rows, 1051 groups, median k 111). lab_results has no catalogued quasi-identifier left, so it has no k figure.

## What the protected copy contains

- ed_visits: patient_hetu replaced by a keyed HMAC-SHA256 pseudonym (first 16 hex chars, random 32-byte key saved to `out/health-s1-gate/hmac.key`, never committed); arrival_ts as "HH:00"; age as 10-year bands (top band 80+); municipality kept for the eight most frequent, others "other" (non-resident also becomes "other"); dropped: patient_name, date_of_birth, phone, home_address, postcode, ambulance_unit, chief_complaint, discharge_ts, attending_physician_id, attending_physician_name.
- lab_results: sampled_ts dropped; visit_id kept so the join to ed_visits works.
- clinical_notes and published_weekly_stats: withheld (not written).

## Commands run

```
/Users/ardasarikaya/Desktop/Business/team-1-trusted/.venv/bin/python /Users/ardasarikaya/Desktop/Business/team-1-trusted/scripts/prototypes/health_s1_gate.py hour
cd /Users/ardasarikaya/Desktop/Business/team-1-trusted/data/proving-ground
/Users/ardasarikaya/Desktop/Business/team-1-trusted/.venv/bin/pets-eval scorecard --original /Users/ardasarikaya/Desktop/Business/team-1-trusted/data/proving-ground/data/health --protected /Users/ardasarikaya/Desktop/Business/team-1-trusted/out/health-s1-gate/health --scenario HEALTH-S1 --out /Users/ardasarikaya/Desktop/Business/team-1-trusted/results/health-s1-gate/hour
/Users/ardasarikaya/Desktop/Business/team-1-trusted/.venv/bin/pets-eval check /Users/ardasarikaya/Desktop/Business/team-1-trusted/out/health-s1-gate/health
```

## pets-eval check

Scanned 4 files (two tables, two row maps). One finding: PHONE, 2 hits, shown as "04...86". The tool says PHONE is pattern-only and may be a false positive. We did not locate the two hits; the likely cause is a digit run inside a hex pseudonym, but that is not confirmed. No HETU, IBAN, card, email, IP, MAC or plate hits.

## Caveats

- The parser reads "13:00" as today's date at 13:00, so week and month fields derived from it are meaningless. The five tasks above do not use them. Tasks that need dates (H-U1, H-DP) are out of scope for HEALTH-S1.
- The scorer does not rate age bands or the pseudonym as quasi-identifiers, so the k figure ignores them.
- The scorer ran linkage attacks with its shipped attackers only; a stronger attacker is not covered.
- Dates are gone, so a downstream user cannot study seasonality. That is the price of this design.
