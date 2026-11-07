# HEALTH-S1 score summary

Every number is copied from scorecard.json or computed by `score`. self-assessment, not the official judging score.

## Utility per task

| Task | What it measures | Before | After |
| --- | --- | --- | --- |
| H-U2 | Median length of stay by triage level | not run | 1.0000 |
| H-U4 | Diagnosis-group mix in the eight largest municipalities | not run | 1.0000 |
| H-U6 | 30-day revisit rate by age band (needs readmit_30d or a consistent patient pseudonym) | not run | 0.0271 |
| H-U7 | CRP vs temperature relationship and CRP by diagnosis group (needs visit join) | not run | 1.0000 |
| H-U8 | Hour-of-day arrival curve | not run | 0.0000 |

## Privacy risk components (lower is better)

| Component | Before | After |
| --- | --- | --- |
| ed_visits: direct identifiers retained | not run | 0.0000 |
| ed_visits: records with k<5 | not run | 0.0416 |
| ed_visits: linkage re-identification | not run | 0.0000 |
| ed_visits: free-text identifier leakage | not run | 0.0000 |
| lab_results: direct identifiers retained | not run | 0.0000 |

## k-anonymity (smallest group of rows sharing the same attributes)

- Scorer, ed_visits: columns date_of_birth, sex, municipality, arrival_ts, arrival_mode; k<5 share 0.0416; median k 47.0; min k 1.
- Our own, ed_visits: columns date_of_birth, sex, municipality, arrival_ts; k<5 share 0.0075; min k 1.

## Residual risk

ed_visits, records with k<5, is 0.0416: 4.2% of the records share their quasi-identifier combination with fewer than 5 rows, so an attacker who knows those attributes about a person can narrow the match to a handful of rows or one.

Attacker model: the toolkit's shipped attackers only. Attacks run: linkage re-identification with the shipped attacker files, a dictionary attack on hashed columns, a direct-identifier pattern scan, and k over the quasi-identifiers in the field catalogue. Stronger attackers (more background knowledge, other outside data) were not tested.

## Scores

- Privacy 0.975, utility 0.6054, composite 0.7632 (self-assessment, not the official judging score).
