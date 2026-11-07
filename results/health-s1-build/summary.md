# HEALTH-S1 score summary

Every number is copied from scorecard.json or computed by `score`. self-assessment, not the official judging score.

## Utility per task

| Task | What it measures | Before | After |
| --- | --- | --- | --- |
| H-U2 | Median length of stay by triage level | 1.0000 | 1.0000 |
| H-U4 | Diagnosis-group mix in the eight largest municipalities | 1.0000 | 0.8744 |
| H-U6 | 30-day revisit rate by age band (needs readmit_30d or a consistent patient pseudonym) | 1.0000 | 0.9641 |
| H-U7 | CRP vs temperature relationship and CRP by diagnosis group (needs visit join) | 1.0000 | 1.0000 |
| H-U8 | Hour-of-day arrival curve | 1.0000 | 0.9945 |

## Privacy risk components (lower is better)

| Component | Before | After |
| --- | --- | --- |
| clinical_notes: direct identifiers retained | 1.0000 | not released |
| clinical_notes: records with k<5 | 1.0000 | not released |
| clinical_notes: free-text identifier leakage | 1.0000 | not released |
| ed_visits: direct identifiers retained | 1.0000 | 0.0000 |
| ed_visits: records with k<5 | 1.0000 | 0.0000 |
| ed_visits: linkage re-identification | 0.5697 | 0.0000 |
| ed_visits: free-text identifier leakage | 0.0000 | 0.0000 |
| lab_results: direct identifiers retained | 0.0000 | 0.0000 |
| lab_results: records with k<5 | 0.9988 | not released |
| published_weekly_stats: direct identifiers retained | 0.0000 | not released |
| published_weekly_stats: records with k<5 | 0.6573 | not released |

## k-anonymity (smallest group of rows sharing the same attributes)

- Scorer, ed_visits: columns date_of_birth, sex, municipality, arrival_ts; k<5 share 0.0; median k 28.0; min k 5.
- Our own, ed_visits: columns date_of_birth, sex, municipality, arrival_ts; k<5 share 0.0000; min k 5.

## Residual risk

No risk component is above zero.

Attacker model: the toolkit's shipped attackers only. Attacks run: linkage re-identification with the shipped attacker files, a dictionary attack on hashed columns, a direct-identifier pattern scan, and k over the quasi-identifiers in the field catalogue. Stronger attackers (more background knowledge, other outside data) were not tested.

## Scores

- Privacy 1.0, utility 0.9666, composite 0.9845 (self-assessment, not the official judging score).
- Before: privacy 0.1716, utility 1.0, composite 0.2752.
