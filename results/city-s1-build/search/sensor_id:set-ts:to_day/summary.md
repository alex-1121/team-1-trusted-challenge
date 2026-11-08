# CITY-S1 score summary

Every number is copied from scorecard.json or computed by `score`. self-assessment, not the official judging score.

## Utility per task

| Task | What it measures | Before | After |
| --- | --- | --- | --- |
| CITY-U1 | Footfall by zone x hour x weekday/weekend | not run | 0.7447 |
| CITY-U5 | Black Friday uplift vs previous Friday | not run | 0.8491 |

## Privacy risk components (lower is better)

| Component | Before | After |
| --- | --- | --- |
| wifi_probes: direct identifiers retained | not run | 0.0000 |
| wifi_probes: records with k<5 | not run | 0.0000 |
| wifi_probes: trajectory unicity (mac) | not run | 0.8800 |

## k-anonymity (smallest group of rows sharing the same attributes)

- Scorer, wifi_probes: columns sensor_id, ts; k<5 share 0.0; median k 168.0; min k 5.
- Our own: columns sensor_id, ts; k<5 share 0.0000; min k 5.

## Residual risk

wifi_probes, trajectory unicity (mac), is 0.88: 88.0% of this risk remains.

Attacker model: the toolkit's shipped attackers only. Attacks run: linkage re-identification with the shipped attacker files, a dictionary attack on hashed columns, a direct-identifier pattern scan, and k over the quasi-identifiers in the field catalogue. Stronger attackers (more background knowledge, other outside data) were not tested.

## Scores

- Privacy 0.4133, utility 0.7969, composite 0.5291 (self-assessment, not the official judging score).
