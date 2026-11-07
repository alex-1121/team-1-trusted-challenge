# ENERGY-S3 score summary

Every number is copied from scorecard.json or computed by `score`. self-assessment, not the official judging score.

## Utility per task

| Task | What it measures | Before | After |
| --- | --- | --- | --- |
| ENERGY-U3 | Temperature sensitivity (kWh/day per °C) by heating type | not run | 1.0000 |
| ENERGY-U4 | Heating-type classifier: train on protected, test on original | not run | 1.0000 |
| ENERGY-U7 | Winter consumption by late-payment group × electric heating | not run | 1.0000 |

## Privacy risk components (lower is better)

| Component | Before | After |
| --- | --- | --- |
| customers: direct identifiers retained | not run | 0.0000 |
| customers: records with k<5 | not run | 0.0000 |
| customers: linkage re-identification | not run | 0.0000 |
| customers: free-text identifier leakage | not run | 0.0000 |
| meter_readings_hourly: direct identifiers retained | not run | 0.0000 |
| meter_readings_hourly: records with k<5 | not run | 0.0000 |

## k-anonymity (smallest group of rows sharing the same attributes)

- Scorer, customers: columns heating_type; k<5 share 0.0; median k 453.0; min k 20.
- Scorer, meter_readings_hourly: columns ts; k<5 share 0.0; median k 757.0; min k 757.
- Our own: columns ts; k<5 share 0.0000; min k 757.

## Residual risk

No risk component is above zero.

Attacker model: the toolkit's shipped attackers only. Attacks run: linkage re-identification with the shipped attacker files, a dictionary attack on hashed columns, a direct-identifier pattern scan, and k over the quasi-identifiers in the field catalogue. Stronger attackers (more background knowledge, other outside data) were not tested.

## Scores

- Privacy 1.0, utility 1.0, composite 1.0 (self-assessment, not the official judging score).
