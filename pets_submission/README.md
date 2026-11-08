# pets_submission: HEALTH-S1 release for the organisers' optional checks

Built from commit 4847116 with `python -m pets_transformer.cli build --scenario HEALTH-S1`.
Gate result: red-team gate pass on the first build, no refusal. Details: `results/health-s1-build/` on main describes the same pipeline; this build's own report was not committed.

## Files

- `health/ed_visits.csv`, `health/lab_results.csv`: the protected tables.
- `health/rowmap_ed_visits.csv`, `health/rowmap_lab_results.csv`: one row per protected row, giving the original record id. These are the answer key.
- `unseen_field_labels.csv`: our labels for the unseen HR export (`column,privacy_role,subtype`).
- `health_field_labels.csv`: our labels for the health tables.
- `release_record.json`: the signed policy, the hash of every released file, the recipient and the recipient's duties.

No HMAC key is stored anywhere: a fresh key is drawn per build and lives only in memory.

## Handling

- This folder is where the organisers' guide asks for it (`context/proving-ground/docs/EVALUATION.md`, "Optional organiser checks"): in the repository, which stays private.
- The row maps are the answer key. They must never be published: if the repository ever goes public, remove `pets_submission/health/` and `release_record.json` from it first.
- `.gitattributes` marks the protected tables, the row maps and the release record `export-ignore`, so `git archive` (how the source zip is built) leaves them out. The two label files stay in the zip.
- customer_service text redaction was not done.
