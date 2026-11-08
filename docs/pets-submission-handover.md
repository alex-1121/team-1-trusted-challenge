# pets_submission/: what it holds and how it could reach the organisers

The organisers may ask, during the event, for a `pets_submission/` folder so they can run their hidden checks: stronger attackers, the private labels for the `unseen` export and hidden evaluation spans (`context/what-is-expected.md`, "What we hand in on Sunday").

## What the folder holds

`python -m pets_transformer.cli build --scenario HEALTH-S1` fills it (`README.md`, "Make a protected copy of the data for a scenario"; every option in `technical-details.md`, "How to run (every option)"), and only when the red-team gate and the utility check pass (`results/health-s1-build/redteam.json`):

- `pets_submission/health/ed_visits.csv` and `pets_submission/health/lab_results.csv`: the protected tables. Not committed.
- `pets_submission/health/rowmap_ed_visits.csv` and `pets_submission/health/rowmap_lab_results.csv`: one row per protected row, giving the original record id. Not committed.
- `pets_submission/unseen_field_labels.csv`: the detector's labels for the unseen HR export, format `column,privacy_role,subtype`. Committed.
- `pets_submission/health_field_labels.csv`: the detector's labels for the health tables. Committed.
- `pets_submission/release_record.json`: the signed policy the release was built under, the hash of every released file, the recipient and the recipient's duties. Not committed here; the copy in `results/` is.

The HMAC key is not in the folder. A fresh key is drawn for every build and exists only in memory, so it cannot be handed over or leak. The row maps still link every token to an original id, which is why they stay private.

## Why row maps must not be published

- A row map links each protected row back to the original record. Together with the original data it is the answer key that tells an attacker, or a judge, which guess is right.
- The organiser rule says `rowmap_*.csv` are never published anywhere (`AGENTS.md`, "Data rules"). The repo goes public for the submission, so the row maps cannot go into git, the source zip or a release.
- `.gitignore` blocks `**/rowmap_*.csv` and everything in `pets_submission/` except the two label files.

## Open question (for the TrustED Discord channel)

How do the organisers want to receive `pets_submission/` when it contains row maps? Status: **open**. Nobody has asked or answered it yet. Until there is an answer, the folder stays on our machines.

## Candidate handover routes (proposals, not decided)

1. **Proposal A: a private upload the organisers name.** We ask on Discord and use whatever private channel they give (a private file drop or a direct message with an attachment). Nothing goes public. It depends on them naming a channel.
2. **Proposal B: an encrypted archive, key sent separately.** We encrypt the folder (for example a 7-Zip archive with AES-256 and a long random password), share the archive through any channel, and send the password to one named organiser by a different channel. The archive alone reveals nothing if it leaks. The risk moves to the password: whoever holds both can read the row maps.

The team picks one after the Discord answer, and logs it as a row in `decisions.md`.
