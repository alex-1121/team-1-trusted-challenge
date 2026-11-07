# Plan: select, repair, attack - a release gate on top of the HEALTH-S1 build

Status: proposed, implemented on the local branch `fix/release-gate` (from main at 7cf541b, not pushed). Author: Claude Opus 5.5, run by Tadek, 2026-11-07. Comment as PR review comments or inline `> note (name):` lines. Every number below is copied from the committed JSON named next to it (self-assessment from the organisers' `pets-eval`, not the official judging score).

## TL;DR

The release on main at 7cf541b scores composite 0.9709 but leaks what it claims to remove: the dropped arrival date comes back from the order of the visits (1.0 of rows), 10 news-clip patients are re-identified with it, and the patient pseudonym makes 0.3544 of patients unique by their visit fingerprint (`results/redteam/before-7cf541b.json`). This branch turns the pipeline into: **detect, select, protect, repair, score, attack, refuse or release**.

- **Select** writes the scenario contract itself: every column gets a ladder of candidate PETs for its detected type, most private first, and keeps the first one under which every required task stays within 0.05 of the exact-data reference (`src/pets_transformer/selector.py`, evidence `results/selection/HEALTH-S1.json`). This is objective 2 done by the tool, not by hand.
- **Protect** tokenises record keys (keyed HMAC, joins survive, no order) and writes every table in a random row order.
- **Repair** coarsens only the rows still in a group with k<5 or fewer than 2 distinct diagnoses, and picks the order of its steps by scoring every order.
- **Attack** runs five attacks the scorecard does not run; **refuse** blocks `pets_submission/` when one succeeds or when a required task falls under 0.5.

Result for HEALTH-S1: privacy 1.0, utility 0.9588, composite 0.9808, every attack at 0 or below its threshold (`results/health-s1-build/`). The same code, with no hand-written rules, serves HEALTH-S3 (composite 1.0) and EDU-S2 (0.9983), and refuses PUB-S3, which our PET library cannot serve.

## Findings on main at 7cf541b

Source: `results/redteam/before-7cf541b.json` (release built by main's own code).

| Attack | Result | Threshold |
|---|---|---|
| Order attack: dates rebuilt from file order / sorted `visit_id` / first `lab_id` per visit | 0.9975 / 1.0 / 1.0 | 0.05 |
| News-clip linkage with rebuilt dates | 10 of 220 clips, all correct (0.0455) | 0 |
| Person fingerprint via the patient pseudonym | 0.3544 of patients, 0.8464 of the 9885 repeat patients | 0.05 |
| Organisers' linkage attacker, band-aware | 0.0 | 0.01 |
| Plain hashes | 0.0 | 0 |

Root causes: the role rule "record_key: keep" kept a sequential key; protect wrote rows in the original order; the pseudonym linked visits. Also found: the organisers' linkage attacker reads `date_of_birth` as a date and "HH:00" as today's date, so its 0.0 on that release was partly an artefact. Our band-aware rerun of the same attacker also finds 0.0 on both releases, because without a date it holds only place, age and sex (median candidate set in the hundreds); the date leak is what the order attack catches.

## What changed

| # | Change | Where |
|---|---|---|
| 1 | `token` PET: keyed HMAC-SHA256 with a prefix, same value same token across tables | `pets.py`, `protect.py` |
| 2 | Every released table shuffled with a cryptographic random permutation; row map follows | `protect.py` |
| 3 | Fresh HMAC key per build, so tokens of two releases cannot be joined | `build.py` |
| 4 | New PETs for the selector: month, ISO week, date, coordinate grid (decimals), postcode prefix | `pets.py` |
| 5 | Selector: candidate ladders per type, ablation against the exact-data reference, reasons with the measured scores; the build runs it when no reviewed contract exists | `selector.py`, `build.py`, `cli.py select` |
| 6 | `contracts/HEALTH-S1.json` is now the selector's output; the hand-written contract is kept as `contracts/HEALTH-S1.handwritten.json` for comparison | `contracts/` |
| 7 | Repair: local recoding of at-risk rows (k<5 or l<2), join flags for tables joined on the key, suppression, row drop as last resort; search over step orders | `repair.py` |
| 8 | Red team: order attack, news-clip linkage, person fingerprint (pseudonyms and repeating tokens), the organisers' linkage attacker made band-aware, plain-hash reversal | `redteam.py`, `cli.py redteam` |
| 9 | Gate: build refuses `pets_submission/` when an attack passes its threshold or a required task scores under 0.5 | `build.py` |
| 10 | Per-run results: `results/<scenario>-build/` holds the scorecard, repair search, checks and red team | `build.py`, `checks.py` call |
| 11 | Tests for tokens, shuffle, repair, l-diversity, order attack, plain hashes, selector | `tests/test_release_gate.py` |

## Results

| Release | Privacy | Utility | Composite | Gate | Source |
|---|---|---|---|---|---|
| HEALTH-S1 raw | 0.1716 | 1.0 | 0.2752 | - | `baseline-scores/health_HEALTH-S1_research-env_raw.json` |
| HEALTH-S1 main at 7cf541b | 0.9533 | 0.9928 | 0.9709 | fail | `results/redteam/before-7cf541b.json` |
| **HEALTH-S1, selected contract** | **1.0** | **0.9588** | **0.9808** | **pass** | `results/health-s1-build/` |
| HEALTH-S1, without the lab join flag | 1.0 | 0.982 | 0.9918 | pass | `results/health-s1-noflag-build/` |
| HEALTH-S1, hand-written contract | 1.0 | 0.9666 | 0.9845 | pass | `results/health-s1-handwritten-build/` |
| HEALTH-S1, with the patient pseudonym | 1.0 | 0.9588 | 0.9808 | fail (fingerprint 0.2906) | `results/health-s1-pseudonym-build/` |
| HEALTH-S3 (AI vendor), selected | 1.0 | 1.0 | 1.0 | pass | `results/health-s3-build/` |
| EDU-S2 (edtech vendor), selected | 1.0 | 0.9963 | 0.9983 | pass | `results/edu-s2-build/` |
| PUB-S3 (equity research), selected | 1.0 | 0.2222 | 0.386 | fail (utility) | `results/pub-s3-build/` |

Raw baselines for the others: HEALTH-S3 0.2769, EDU-S2 0.3395, PUB-S3 0.1429 (`baseline-scores/`).

## Open for the team

1. **Lab join flag.** The researchers hold both tables, so "this visit had lab tests" is visible in the release. With the flag the repair keeps every visit with labs in a group of at least 5 such visits (joined k<5 share 0.0, `results/health-s1-build/checks/joined_k.json`); without it the composite is 0.9918 instead of 0.9808 and 0.0521 of those visits sit in smaller groups (`results/health-s1-noflag-build/checks/joined_k.json`). We chose the flag. Remove `join_flags` from `k_target` to flip it.
2. **Patient pseudonym.** The organisers' suggested target for HEALTH-S1 asks for one (`metadata/scenarios.json`). Keeping it fails our gate: 0.2906 of patients are unique by fingerprint (`results/health-s1-pseudonym-build/redteam.json`). No HEALTH-S1 task needs it (H-U6 reads `readmit_30d`). We dropped it and say why.
3. **Gate thresholds** (0.05 order attack, 0 news clips, 0.05 fingerprint, 0.01 band-aware linkage, 0 plain hashes, 0.5 utility floor) are our choice, stated in every `redteam.json`.
4. **PUB-S3 is refused.** Its three tasks need two dates, a postcode and coordinates at row level; with k of at least 5 the repair has to suppress most rows. Aggregation or synthetic data would be the right PET; neither is in the library.

## Known limits

- An attacker who already knows a visit's diagnosis group, age band, municipality and arrival hour singles out 0.0964 of visits (`results/health-s1-build/checks/informed_attacker.json`). Adding the diagnosis group to the k key would put most rows at risk.
- The detector reads the first 5000 rows of each table; on a time-sorted table that is the first weeks. Changing it now would contaminate the held-out detector scores, so it is left as it is.
- The extra checks (`checks.py`) are written for the health ED tables; on other datasets the build writes `checks/not_run.txt`.
- The energy dataset (1.6 million hourly readings) was not built: the build stopped without output on this machine.
