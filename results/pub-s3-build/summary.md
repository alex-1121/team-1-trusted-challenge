# PUB-S3 score summary

Every number is copied from scorecard.json or computed by `score`. self-assessment, not the official judging score.

## Utility per task

| Task | What it measures | Before | After |
| --- | --- | --- | --- |
| PUB-U1 | Request counts by area (3-digit postcode) x category x month | 1.0000 | 0.0000 |
| PUB-U2 | Median resolution time by category | 1.0000 | 0.0000 |
| PUB-U3 | Hotspot map: top-50 1 km grid cells | 1.0000 | 0.6667 |

## Privacy risk components (lower is better)

| Component | Before | After |
| --- | --- | --- |
| building_permits: direct identifiers retained | 1.0000 | not released |
| building_permits: records with k<5 | 1.0000 | not released |
| service_requests: direct identifiers retained | 1.0000 | 0.0000 |
| service_requests: records with k<5 | 1.0000 | 0.0000 |
| service_requests: linkage re-identification | 0.0000 | 0.0000 |
| service_requests: free-text identifier leakage | 1.0000 | 0.0000 |

## k-anonymity (smallest group of rows sharing the same attributes)

- Scorer, service_requests: columns ts_created, postcode, lat, lon, ts_closed; k<5 share 0.0; median k 16515.0; min k 5.
- Our own: columns ts_created, postcode, lat, lon, ts_closed; k<5 share 0.0000; min k 5.

## Residual risk

No risk component is above zero.

Attacker model: the toolkit's shipped attackers only. Attacks run: linkage re-identification with the shipped attacker files, a dictionary attack on hashed columns, a direct-identifier pattern scan, and k over the quasi-identifiers in the field catalogue. Stronger attackers (more background knowledge, other outside data) were not tested.

## Scores

- Privacy 1.0, utility 0.2222, composite 0.386 (self-assessment, not the official judging score).
- Before: privacy 0.0833, utility 1.0, composite 0.1429.
