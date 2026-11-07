# HEALTH-S3 score summary

Every number is copied from scorecard.json or computed by `score`. self-assessment, not the official judging score.

## Utility per task

| Task | What it measures | Before | After |
| --- | --- | --- | --- |
| H-U2 | Median length of stay by triage level | 1.0000 | 1.0000 |
| H-U3 | Admission prediction: train on protected, test on original/holdout (AUC ratio) | 1.0000 | 1.0000 |
| H-U5 | Distributions of systolic BP, heart rate, temperature and SpO2 | 1.0000 | 1.0000 |

## Privacy risk components (lower is better)

| Component | Before | After |
| --- | --- | --- |
| clinical_notes: direct identifiers retained | 1.0000 | not released |
| clinical_notes: records with k<5 | 1.0000 | not released |
| clinical_notes: free-text identifier leakage | 1.0000 | not released |
| ed_visits: direct identifiers retained | 1.0000 | 0.0000 |
| ed_visits: records with k<5 | 1.0000 | not released |
| ed_visits: linkage re-identification | 0.5424 | 0.0000 |
| ed_visits: free-text identifier leakage | 0.0000 | 0.0000 |
| lab_results: direct identifiers retained | 0.0000 | not released |
| lab_results: records with k<5 | 0.9988 | not released |
| published_weekly_stats: direct identifiers retained | 0.0000 | not released |
| published_weekly_stats: records with k<5 | 0.6573 | not released |

## k-anonymity (smallest group of rows sharing the same attributes)

- Our own: no quasi-identifier is released, so there is no group to count.

## Residual risk

No risk component is above zero.

Attacker model: the toolkit's shipped attackers only. Attacks run: linkage re-identification with the shipped attacker files, a dictionary attack on hashed columns, a direct-identifier pattern scan, and k over the quasi-identifiers in the field catalogue. Stronger attackers (more background knowledge, other outside data) were not tested.

## Scores

- Privacy 1.0, utility 1.0, composite 1.0 (self-assessment, not the official judging score).
- Before: privacy 0.1728, utility 1.0, composite 0.2769.
