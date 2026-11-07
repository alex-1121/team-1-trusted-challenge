# Plan: select, repair, attack - a release gate on top of the HEALTH-S1 build

Status: implemented on branch `fix/release-gate` (from main at 7cf541b) and fast-forwarded into main on 2026-11-07. Author: Claude Opus 5.5, run by Tadek, 2026-11-07. Comment as PR review comments or inline `> note (name):` lines. Every number below is copied from the committed JSON named next to it (self-assessment from the organisers' `pets-eval`, not the official judging score).

## TL;DR

The release on main at 7cf541b scores composite 0.9709 but leaks what it claims to remove: the dropped arrival date comes back from the order of the visits (1.0 of rows), 10 news-clip patients are re-identified with it, and the patient pseudonym makes 0.3544 of patients unique by their visit fingerprint (`results/redteam/before-7cf541b.json`). This branch turns the pipeline into: **detect, select, protect, repair, score, attack, refuse or release**.

- **Select** writes the scenario contract itself: every column gets a ladder of candidate PETs for its detected type, most private first, and keeps the first one under which every required task stays within 0.05 of the exact-data reference (`src/pets_transformer/selector.py`, evidence `results/selection/HEALTH-S1.json`). This is objective 2 done by the tool, not by hand.
- **Protect** tokenises record keys (keyed HMAC, joins survive, no order) and writes every table in a random row order.
- **Repair** coarsens only the rows still in a group with k<5 or fewer than 2 distinct diagnoses, writes what it coarsened as explicit ranges, and picks the order of its steps by scoring every order. The selector then re-scores its choices on the repaired release, so it never keeps a column so fine that the repair wipes it out.
- **Attack** runs five attacks the scorecard does not run; **refuse** blocks `pets_submission/` when one succeeds or when a required task falls under 0.5.

Result for HEALTH-S1: privacy 1.0, utility 0.971, composite 0.9866, every attack at 0 or below its threshold (`results/health-s1-build/`). The same code, with no hand-written rules, serves HEALTH-S3 (composite 1.0) and EDU-S2 (0.9983); ENERGY-S3 (energy-poverty research, 1.6 million hourly readings) reaches composite 1.0 once the time ladder offers date and hour together. It refuses PUB-S3: with a reviewer's edit (a duration instead of two timestamps) its main question scores 0.9767, but the area counts and the 1 km hotspot map cannot both survive k of at least 5 in one row-level table.

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
| 12 | Repaired hours are written as explicit ranges ("06:00 to 08:59"), not as a block start that reads like an exact hour; the red team and checks treat a coarsened value as a match for every value it can stand for | `repair.py`, `generalise.py`, `redteam.py` |
| 13 | Checks (l-diversity, informed attacker, joined k) read the contract's k target, so they run on any dataset; the informed attacker knows the k columns at the release's own precision plus the sensitive fact | `checks.py` |
| 14 | Optional `informed` rule in the k target: no row unique even for an attacker who knows the sensitive fact (diagnosis group) | `repair.py`, `protect.py`, `contracts/HEALTH-S1-informed.json` |
| 15 | Selector scores every kept quasi-identifier again on the repaired release and moves it to a more private rung when the tasks keep at least the same mean score | `selector.py` |
| 16 | New PETs: date and hour (for tasks that need both), duration (the interval instead of two timestamps); repair op to_day | `pets.py`, `protect.py`, `repair.py` |
| 17 | Red team: the organisers' attack specs run on every released table; the fingerprint counts only per-person facts (a per-row timestamp is not one) | `redteam.py` |
| 18 | Detector: a column judged non-sensitive on the first 5000 rows gets a second look on rows from the whole file and can only move to a more protective label | `detect.py`, `results/detect/RESULTS.md` |

## Results

| Release | Privacy | Utility | Composite | Gate | Source |
|---|---|---|---|---|---|
| HEALTH-S1 raw | 0.1716 | 1.0 | 0.2752 | - | `baseline-scores/health_HEALTH-S1_research-env_raw.json` |
| HEALTH-S1 main at 7cf541b | 0.9533 | 0.9928 | 0.9709 | fail | `results/redteam/before-7cf541b.json` |
| **HEALTH-S1, selected contract** | **1.0** | **0.971** | **0.9866** | **pass** | `results/health-s1-build/` |
| HEALTH-S1, without the lab join flag | 1.0 | 0.9826 | 0.992 | pass | `results/health-s1-noflag-build/` |
| HEALTH-S1, closing the informed attacker | 1.0 | 0.9255 | 0.9647 | pass | `results/health-s1-informed-build/` |
| HEALTH-S1, hand-written contract | 1.0 | 0.9734 | 0.9877 | pass | `results/health-s1-handwritten-build/` |
| HEALTH-S1, with the patient pseudonym | 1.0 | 0.971 | 0.9866 | fail (fingerprint 0.2935) | `results/health-s1-pseudonym-build/` |
| HEALTH-S3 (AI vendor), selected | 1.0 | 1.0 | 1.0 | pass | `results/health-s3-build/` |
| EDU-S2 (edtech vendor), selected | 1.0 | 0.9963 | 0.9983 | pass | `results/edu-s2-build/` |
| ENERGY-S3 (energy-poverty research), selected | 1.0 | 1.0 | 1.0 | pass | `results/energy-s3-build/` |
| PUB-S3 (equity research), selected | 1.0 | 0.2131 | 0.3734 | fail (utility) | `results/pub-s3-auto-build/` |
| PUB-S3, selected then reviewed | 1.0 | 0.5547 | 0.7327 | fail (utility: PUB-U1 0.3888, PUB-U3 0.2987) | `results/pub-s3-build/` |

Raw baselines for the others: HEALTH-S3 0.2769, EDU-S2 0.3395, ENERGY-S3 0.3506, PUB-S3 0.1429 (`baseline-scores/`). The hand-written contract scores 0.0011 higher than the selected one, but leaves 0.121 of visits with lab results in groups of fewer than 5 such visits and lets the informed attacker single out 0.1599 of visits (`results/health-s1-handwritten-build/checks/`).

## Open for the team

1. **Lab join flag.** The researchers hold both tables, so "this visit had lab tests" is visible in the release. With the flag the repair keeps every visit with labs in a group of at least 5 such visits (joined k<5 share 0.0, `results/health-s1-build/checks/joined_k.json`); without it the composite is 0.992 instead of 0.9866 and 0.055 of those visits sit in smaller groups (`results/health-s1-noflag-build/checks/joined_k.json`). We chose the flag. Remove `join_flags` from `k_target` to flip it.
2. **Informed attacker.** One who already knows a visit's diagnosis group, age band, municipality and arrival hour singles out 0.0971 of visits on the selected release, 0.9294 of them correctly (`results/health-s1-build/checks/informed_attacker.json`). `contracts/HEALTH-S1-informed.json` adds one rule to the k target (no row unique once the diagnosis group is known) and an 8-hour block to the repair ladder: the attacker singles out 0.0, at composite 0.9647 instead of 0.9866; the diagnosis mix by municipality (H-U4) falls to 0.8334 and the arrival curve (H-U8) to 0.8485 (`results/health-s1-informed-build/`). We kept the selected contract as the default because HEALTH-S1 is a known recipient under an agreement; for a less trusted recipient the informed contract is the one to ship.
3. **Patient pseudonym.** The organisers' suggested target for HEALTH-S1 asks for one (`metadata/scenarios.json`). Keeping it fails our gate: 0.2935 of patients are unique by fingerprint (`results/health-s1-pseudonym-build/redteam.json`). No HEALTH-S1 task needs it (H-U6 reads `readmit_30d`). We dropped it and say why.
4. **Gate thresholds** (0.05 order attack, 0 news clips, 0.05 fingerprint, 0.01 band-aware linkage, 0 plain hashes, 0.5 utility floor) are our choice, stated in every `redteam.json`.
5. **PUB-S3 is refused.** The selector's own contract fails (PUB-U1 and PUB-U2 0): the two timestamps, postcode and coordinates make nearly every row unique. `contracts/PUB-S3.json` is the reviewed version: month of creation, 3-digit postcode, 1 km grid, and the closing time replaced by `resolution_hours` (the new duration PET), with the organisers' suggested k key (postcode, category, month, language) plus the grid. The research question itself (PUB-U2, resolution time) then scores 0.9767, but with the grid in the key 0.9074 of rows start at risk, 5219 end suppressed (`results/pub-s3-build/repair_report.json`), and the area counts (0.3888) and the hotspot map (0.2987) stay under the 0.5 floor. A hotspot map is an aggregate; releasing it as cell counts is the right PET, and the organisers' scorer reads only row-level coordinates.

## Known limits

- The detector's rules still read the first 5000 rows; the wide-sample second look only adds protection. Its health result is not a clean held-out result (`results/detect/RESULTS.md`).
- The selector's post-repair pass moves one column one rung at a time; when tasks need several columns to move together (PUB-S3) it can stop at a poor choice. The evidence is in each `selection.json`.
- HEALTH-S3 and EDU-S2 release no quasi-identifier at all, so they have no k target and the extra checks do not apply (`checks/not_run.txt`).
- ENERGY-S3 releases each meter's hourly series under a keyed token, with heating type and the late-payment count; its tasks need the series per meter. No attack in its threat model links a series to a person (the organisers' directory attack finds no quasi-identifier left, `results/energy-s3-build/redteam.json`). A neighbour who knows their own consumption, or a vacation post matched to a drop in consumption, is in the threat model of ENERGY-S1 and S2, not S3, and was not built. The build takes several minutes and a few GB of memory on a laptop.
