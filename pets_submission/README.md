# pets_submission: our labels for the organisers' optional checks

The organisers' guide asks for this folder (`context/proving-ground/docs/EVALUATION.md`, "Optional organiser checks").

## Committed files

- `unseen_field_labels.csv`: our labels for the unseen HR export (`column,privacy_role,subtype`).
- `health_field_labels.csv`: our labels for the health tables.

## What a build adds, never committed

`python -m pets_transformer.cli build --scenario HEALTH-S1` also writes the protected tables (`health/ed_visits.csv`, `health/lab_results.csv`), their row maps (`health/rowmap_*.csv`, one row per protected row giving the original record id, the answer key for scoring) and `release_record.json` (the signed policy, the hash of every released file, the recipient and the recipient's duties). `.gitignore` keeps them out of git and `.gitattributes` keeps them out of the source zip.

During judging, the HEALTH-S1 release built from commit 4847116 was kept here, in the then-private repository, for the organisers' checks. It was removed from the tree when judging ended (see `decisions.md`, 2026-11-09).

No HMAC key is stored anywhere: a fresh key is drawn per build and lives only in memory.

customer_service text redaction was not done.
