# EDU-S2 score summary

Every number is copied from scorecard.json or computed by `score`. self-assessment, not the official judging score.

## Utility per task

| Task | What it measures | Before | After |
| --- | --- | --- | --- |
| EDU-U2 | Drop-out prediction AUC: train on protected, test on original hold-out | 1.0000 | 0.9926 |
| EDU-U4 | Spearman correlation of unexcused absence hours with mean grade | 1.0000 | 1.0000 |

## Privacy risk components (lower is better)

| Component | Before | After |
| --- | --- | --- |
| absences: direct identifiers retained | 0.0000 | 0.0000 |
| absences: records with k<5 | 0.0000 | not released |
| counsellor_notes: direct identifiers retained | 1.0000 | not released |
| counsellor_notes: records with k<5 | 0.2618 | not released |
| counsellor_notes: free-text identifier leakage | 1.0000 | not released |
| course_grades: direct identifiers retained | 1.0000 | 0.0000 |
| course_grades: records with k<5 | 0.5110 | not released |
| matriculation_results: direct identifiers retained | 0.0000 | not released |
| matriculation_results: records with k<5 | 0.0125 | not released |
| students: direct identifiers retained | 1.0000 | 0.0000 |
| students: records with k<5 | 1.0000 | not released |
| students: linkage re-identification | 0.9593 | 0.0000 |

## k-anonymity (smallest group of rows sharing the same attributes)

- Our own: no quasi-identifier is released, so there is no group to count.

## Residual risk

No risk component is above zero.

Attacker model: the toolkit's shipped attackers only. Attacks run: linkage re-identification with the shipped attacker files, a dictionary attack on hashed columns, a direct-identifier pattern scan, and k over the quasi-identifiers in the field catalogue. Stronger attackers (more background knowledge, other outside data) were not tested.

## Scores

- Privacy 1.0, utility 0.9963, composite 0.9983 (self-assessment, not the official judging score).
- Before: privacy 0.219, utility 1.0, composite 0.3395.
