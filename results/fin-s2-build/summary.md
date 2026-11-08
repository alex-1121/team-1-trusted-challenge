# FIN-S2 score summary

Every number is copied from scorecard.json or computed by `score`. self-assessment, not the official judging score.

## Utility per task

| Task | What it measures | Before | After |
| --- | --- | --- | --- |
| FIN-U1 | Fraud model: train on protected Jul–Oct, test on original Nov–Dec (PR-AUC ratio) | 1.0000 | 0.7966 |
| FIN-U4 | Card spending-profile segmentation (k=6) agreement | 1.0000 | not evaluated |
| FIN-U6 | Mean monthly card spend by income band × age band | 1.0000 | not evaluated |

## Privacy risk components (lower is better)

| Component | Before | After |
| --- | --- | --- |
| card_transactions: direct identifiers retained | 1.0000 | 0.0000 |
| card_transactions: records with k<5 | 1.0000 | 0.0015 |
| card_transactions: linkage re-identification | 1.0000 | 0.0000 |
| cards: direct identifiers retained | 1.0000 | not released |
| cards: records with k<5 | 1.0000 | not released |
| customers: direct identifiers retained | 1.0000 | not released |
| customers: records with k<5 | 1.0000 | not released |
| customers: linkage re-identification | 0.9020 | not released |
| transfers: direct identifiers retained | 1.0000 | not released |
| transfers: records with k<5 | 1.0000 | not released |
| transfers: free-text identifier leakage | 1.0000 | not released |

## k-anonymity (smallest group of rows sharing the same attributes)

- Scorer, card_transactions: columns amount_eur, currency; k<5 share 0.0015; median k 73.0; min k 1.
- Our own: columns amount_eur; k<5 share 0.0000; min k 5.

## Residual risk

card_transactions, records with k<5, is 0.0015: 0.1% of the records share their quasi-identifier combination with fewer than 5 rows, so an attacker who knows those attributes about a person can narrow the match to a handful of rows or one.

Attacker model: the toolkit's shipped attackers only. Attacks run: linkage re-identification with the shipped attacker files, a dictionary attack on hashed columns, a direct-identifier pattern scan, and k over the quasi-identifiers in the field catalogue. Stronger attackers (more background knowledge, other outside data) were not tested.

## Scores

- Privacy 0.999, utility 0.2655, composite 0.4429 (self-assessment, not the official judging score).
- Before: privacy 0.0045, utility 1.0, composite 0.0081.
