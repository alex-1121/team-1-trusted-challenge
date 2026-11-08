# FIN-S2 score summary

Every number is copied from scorecard.json or computed by `score`. self-assessment, not the official judging score.

## Utility per task

| Task | What it measures | Before | After |
| --- | --- | --- | --- |
| FIN-U1 | Fraud model: train on protected Jul–Oct, test on original Nov–Dec (PR-AUC ratio) | not run | 0.7032 |
| FIN-U4 | Card spending-profile segmentation (k=6) agreement | not run | not evaluated |
| FIN-U6 | Mean monthly card spend by income band × age band | not run | not evaluated |

## Privacy risk components (lower is better)

| Component | Before | After |
| --- | --- | --- |
| card_transactions: direct identifiers retained | not run | 0.0000 |
| card_transactions: records with k<5 | not run | 0.0015 |
| card_transactions: linkage re-identification | not run | 0.0000 |

## k-anonymity (smallest group of rows sharing the same attributes)

- Scorer, card_transactions: columns amount_eur, currency; k<5 share 0.0015; median k 73.0; min k 1.
- Our own: columns amount_eur; k<5 share 0.0000; min k 5.

## Residual risk

card_transactions, records with k<5, is 0.0015: 0.1% of the records share their quasi-identifier combination with fewer than 5 rows, so an attacker who knows those attributes about a person can narrow the match to a handful of rows or one.

Attacker model: the toolkit's shipped attackers only. Attacks run: linkage re-identification with the shipped attacker files, a dictionary attack on hashed columns, a direct-identifier pattern scan, and k over the quasi-identifiers in the field catalogue. Stronger attackers (more background knowledge, other outside data) were not tested.

## Scores

- Privacy 0.999, utility 0.2344, composite 0.4024 (self-assessment, not the official judging score).
