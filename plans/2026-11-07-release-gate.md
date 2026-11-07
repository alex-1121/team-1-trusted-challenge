# Plan: release gate - attack our own release, repair it, refuse to ship it while an attack works

Status: proposed, implemented on branch `fix/release-gate` (from main at 7cf541b). Author: Claude Opus 5.5, run by Tadek, 2026-11-07. Comment as PR review comments or inline `> note (name):` lines.

## TL;DR

The release on main at 7cf541b scores composite 0.9709, but it leaks what it claims to remove. The "dropped" arrival date comes back from the order of the visits, and the patient pseudonym links each person's visits into a fingerprint. This branch adds three things to the pipeline: (1) order-safe output (keyed tokens for record keys, shuffled rows), (2) a repair step that coarsens only the rows still at risk until every group has k of at least 5 and at least 2 distinct diagnoses, choosing the coarsening order by scoring every order, and (3) a red-team gate that runs attacks the organisers' scorecard does not run and blocks `pets_submission/` when one succeeds. The demo story becomes "the official scorer said this was fine, our red team broke it, the tool repaired it".

## Findings on main at 7cf541b (measured; numbers land in results/redteam/)

1. Date rebuilt from order. Sort ed_visits by `visit_id` (sequential, kept as is) and start a new day whenever the hour goes backwards. The same works on the file's own row order and on `lab_results.lab_id`.
2. Person fingerprint. `patient_hetu` becomes a keyed pseudonym, so every visit of a patient links. Age band, sex, municipality and the set of arrival hours single out most repeat patients. No HEALTH-S1 task needs the pseudonym: H-U6 reads `readmit_30d`.
3. k below 5. A share of ed_visits rows sits in groups smaller than 5 (scorer and own k). The sweep only tries one global setting for all rows.
4. Root cause in the design: the role rule "record_key: keep" keeps sequential keys even though the detector flags them as near-sequential.

## Changes

| # | Change | Where |
|---|---|---|
| 1 | New PET `token`: keyed HMAC-SHA256 token with a prefix; the same key and value give the same token in every table, so joins survive | `pets.py`, `protect.py`, contract |
| 2 | `protect_folder` shuffles every released table with a cryptographic random permutation; the row map follows the shuffle | `protect.py` |
| 3 | Contract: `visit_id` (both tables) and `lab_id` become tokens; role rule record_key becomes token; `patient_hetu` dropped with its reason | `contracts/HEALTH-S1.json` |
| 4 | Repair: local recoding of at-risk rows only, ladder of coarsening steps from the contract, final suppression; `search` scores every order of the steps with pets-eval and keeps the best composite that meets the target | `repair.py`, contract `k_target` |
| 5 | Red team: order attack (file order, each unique column, first lab id per visit), news-clip linkage with the rebuilt date, person fingerprint; gate thresholds in the JSON | `redteam.py` |
| 6 | Build: detect, search, protect with the chosen order, score, checks, red team; `pets_submission/` is written only when the gate passes | `build.py`, `cli.py` |
| 7 | Red team run on the release of main at 7cf541b as the "before" evidence | `results/redteam/before-7cf541b.json` |
| 8 | Texts: README demo, guarantee and residual risk, video script, deck outline quote the new JSONs | `README.md`, `docs/` |

## Out of scope

Differential privacy, a second scenario, a learned PET selector, detector changes (its scores stay as committed).

## Open for the team

- Dropping the patient pseudonym removes patient-level linkage for the researchers. The score does not need it; a real study might. The contract states the trade-off; flip the rule back to `pseudonym` and the gate will report the fingerprint risk.
- The red-team thresholds (5% for date rebuild, 5% for singled-out persons) are our choice, stated in the JSON.
