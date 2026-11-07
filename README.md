# TrustED PETs Transformer

Since AI Hackathon 2026, Turku, 6-8 November. TrustED challenge: protect the data, keep its value.

## The challenge

We build a working tool that detects what each column and text field of a synthetic dataset contains. It picks a privacy-enhancing transformation (PET) per data type and sharing scenario, and transforms the data. Then it shows, with measured numbers, what risk was removed and what utility remains.

Status (2026-11-07): HEALTH-S1 is the scored scenario; the build detects, selects, protects, repairs, scores and red-teams in one command, and refuses a release that fails an attack or its purpose (`plans/2026-11-07-release-gate.md`). A multilingual column-type model (`plans/2026-11-07-eu-column-types.md`) runs in advisor mode: the word lists still set every label, the model only flags columns for a person to review (`results/detect-semantic/advisor.json`).

## Start here

1. `context/README.md` - index of every file in `context/` and `team/`; the Layout table below indexes the top level.
2. `context/challenge-digest.md` - the whole challenge in one page.
3. `team/plan.md` - schedule, roles, open questions.

## Layout

One row per top-level file and folder. Files inside `context/` and `team/` are listed one by one in `context/README.md`.

| Path | What it holds |
|---|---|
| `context/` | The official brief, one-pager, video transcript, source file list, challenge digest, and the organiser docs in `context/proving-ground/`. `context/README.md` indexes every file here and in `team/` |
| `team/` | Team plan and the submission checklist |
| `plans/` | Specs, tickets and plans (see `plans/README.md`) |
| `data/` | The proving-ground data, gitignored; `data/README.md` says how to restore it |
| `contracts/` | One JSON contract per scenario: recipient, purpose, role rules (by detected role), named column rules with their reasons, and the k target with its repair ladder. `HEALTH-S1.json` is the selector v2 output; `HEALTH-S1.handwritten.json` the hand-written start; `HEALTH-S1-noflag.json`, `HEALTH-S1-pseudonym.json` and `HEALTH-S1-informed.json` are variants for the team decisions below; `PUB-S3.json` is the selector's PUB-S3 contract after a reviewer's edit; `generated/` holds the contracts the selector wrote for HEALTH-S3, EDU-S2, ENERGY-S3 and PUB-S3 |
| `policy/` | One JSON policy per scenario we build, with the limits the release must meet, the recipient, the purpose and the contract hashes the data steward allows. `build` runs only when the policy's signature verifies against `policy/allowed_signers` (see "Signing a policy" under "How to run") |
| `src/pets_transformer/` | The code: `detect` (labels), `selector` (writes the contract), `pets` and `protect` (the transformations), `repair` (k and l on the rows at risk), `generalise` (what a coarsened value can stand for), `score` (the organisers' scorecard), `checks` and `redteam` (attacks the scorecard does not run), `policy` (the signed limits and the release record), `build` (one command for all of it), `contract`, `sweep` and the command line `cli`; `semantic/` is the optional column-type model (type list, decision rule, features, offline loader and the committed head in `semantic/models/`); by default it only flags columns for review (advisor mode) |
| `tests/` | pytest suite for detect (word lists and the hybrid type model), protect, score, checks, the repair sweep, the release gate (tokens, shuffle, repair, hour ranges, selector, new PETs, attacks), what the gate refuses (`test_gate.py`) and the command-line wiring |
| `scripts/` | One-off scripts; `scripts/prototypes/` holds early experiments, such as the first HEALTH-S1 arrival-time gate; `scripts/semantic/` makes the fake EU test tables and training corpus, the Featherless word lists (`llm_values/`), trains the type model (`train.py`, runbook `TRAINING.md`) and evaluates it |
| `results/` | Committed evidence: detector results (`detect/`), the column-type model's evidence (`detect-semantic/`, indexed in its `README.md`), the selector's evidence (`selection/`), the red-team gate on the earlier release (`redteam/`), the repair sweep (`sweep/`), early gate runs, and one `<scenario>-build/` folder per build (scorecard, repair search, checks, red team), including the HEALTH-S1 variants |
| `baseline-scores/` | "Before" scorecards: every original table scored unprotected, one HTML + JSON pair per scenario, named `<dataset>_<SCENARIO>_<recipient>_raw` |
| `pets_submission/` | What goes to the organisers on request; only the two label files are committed |
| `demo/` | `the-er-register.html`: the demo-video sequence. A printed sheet of patient records is redacted in blue halftone, shuffled, stamped, folded, addressed and sent; it ends on the HEALTH-S1 numbers. One self-contained HTML file, no build step |
| `docs/` | Pitch deck outline, demo video script, what HEALTH-S1 guarantees and its residual risk, and the `pets_submission/` handover |
| `attack_analysis.md` | What `pets-eval` actually measures: risk checks, utility tasks, how the score is aggregated, blind spots |
| `decisions.md` | Team decision log |
| `AGENTS.md` | Rules for every teammate's coding agent |
| `CLAUDE.md` | One line that imports `AGENTS.md` for Claude Code; holds no rules |
| `README.md` | This file |
| `pyproject.toml` | Package definition for `pets_transformer`; optional extras `semantic` (the type model at run time) and `train` (corpus and training) |
| `.gitignore` | Keeps the proving-ground data, the attack answer keys (row maps, truth, holdout), protected tables, bulky outputs, the fake corpus and EU test tables (`data/semantic-*`) and secrets out of git |

## The demo in five items

Every number below is copied from the file named after it in brackets. Scorecard numbers come from the organisers' `pets-eval`. They are our self-assessment and are separate from the official judging score.

### 1. Types found

The detector labels every column from its values alone; it never reads column names. It was tuned on six datasets and scored with `pets-eval detect` on three it did not see while tuning (`results/detect/SPLIT.md`).

| Held-out dataset | macro-F1 | accuracy | sensitive recall |
|---|---|---|---|
| health | 0.8202 (`results/detect/health.json`) | 0.7358 (`results/detect/health.json`) | 0.7442 (`results/detect/health.json`) |
| public_admin | 0.7241 (`results/detect/public_admin.json`) | 0.8108 (`results/detect/public_admin.json`) | 0.8519 (`results/detect/public_admin.json`) |
| customer_service | 0.7821 (`results/detect/customer_service.json`) | 0.7692 (`results/detect/customer_service.json`) | 0.9565 (`results/detect/customer_service.json`) |

The target was macro-F1 above 0.65, the organisers' rule baseline B1 (`results/detect/SPLIT.md`). macro-F1 is the F1 score (a balance of missed and wrong labels) worked out per privacy role and then averaged, so rare roles count as much as common ones; 1.0 is perfect. One caveat: eight rules were added after reading public_admin's errors and the held-out label rows, so public_admin's 0.7241 and customer_service's 0.7821 are not clean held-out scores. Before those rules they were 0.5431 and 0.7462 (`results/detect/RESULTS.md`). The rules read the first 5000 rows of a table, which on a time-sorted table are its first weeks; so a column judged non-sensitive there gets a second look on 5000 rows drawn from the whole file, and can only move to a more protective label. That moved one held-out column, health `icd10_secondary`, to diagnosis code: health macro-F1 0.8086 to 0.8202. The change was narrowed after seeing held-out results, so this health score is not a clean held-out score either (`results/detect/RESULTS.md`).

The same detector labelled the organisers' unlabelled HR export: 26 columns in `results/detect/unseen_field_labels.csv`, format `column,privacy_role,subtype`. The organisers hold the answers, so we have no score for it.

**A multilingual model that flags the columns the word lists may have missed** (`plans/2026-11-07-eu-column-types.md`). The word lists know Finnish names and towns; a German surname or a Polish occupation falls through to "category", which is treated as harmless. A small multilingual sentence encoder (`intfloat/multilingual-e5-small`, MIT licence, runs offline on CPU) plus a classifier head trained only on fake data gives such columns one of ten types with calibrated probabilities. We tested two ways to use it. In hybrid mode a word-list match stands and the model labels the fall-through columns. Results, development data first and a test split run once (`results/detect-semantic/SPLIT.md`):

| Check (test split) | Word lists only | Word lists + model |
|---|---|---|
| Fake tables from countries never trained on, macro-F1 | cs 0.5963, pt 0.5553, hu 0.5053 | cs 0.7709, pt 0.6976, hu 0.6806 (`results/detect-semantic/e2_eu_test.json`) |
| Name, address, town, occupation and similar columns labelled harmless there | - | 0 in each country (`results/detect-semantic/e2_eu_test.json`) |
| Calibration error (gap between stated and actual confidence) | - | 0.0218 (`results/detect-semantic/e3_calibration_test.json`) |
| Proving-ground held-out macro-F1: health, public_admin, customer_service | 0.8202, 0.7241, 0.7821 | 0.7879, 0.7084, 0.7786 (`results/detect-semantic/e1_proving_ground_test.json`) |
| Detect time, all nine datasets, laptop CPU | 22.4 s | 54.8 s (`results/detect-semantic/e5_cost.json`) |

The test split was run once, on commit `68aa116` (tag `evidence/68aa116`), before the review fixes to hybrid (the second look at rows from the whole file now runs before the model, so hybrid can no longer end less protective than the word lists). Those numbers were not rerun, so the test-split rows describe hybrid as it was then. The detect-time row is from the rerun after the fixes, on commit `cf054d6` (tag `evidence/cf054d6`). Details in `results/detect-semantic/SPLIT.md`.

The proving-ground row is a miss: the model read lab test codes and a permit type as place or organisation names, confidently, so no warning was raised. So the default is advisor mode, decided after the test run (`results/detect-semantic/SPLIT.md`): the word lists set every label, exactly as before, and the model only adds a review flag when it would treat a column differently. Labels and proving-ground scores are therefore unchanged. Its flags (`results/detect-semantic/advisor.json`; "right" means the word-list label really was wrong):

| Data | Columns | Word-list label wrong | Flagged | Flag right | False alarm |
|---|---|---|---|---|---|
| Fake EU tables, countries never trained on (cs, pt, hu) | 66 | 42 | 28 | 28 | 0 |
| Proving ground, held out (health, public_admin, customer_service) | 129 | 30 | 11 | 5 | 6 |
| Proving ground, tuning datasets | 346 | 39 | 23 | 7 | 16 |

On foreign data every flag points at a real mistake. On the Finnish proving ground about half the flags on held-out data are false alarms, most of them the model doubting a correct word-list match. A flag says "look at this column", not what the right label is. Next step: add types for codes, medical and education terms and number formats, and train on real tables from EU open-data portals (no personal data in them), with names and addresses kept fake. Limitations: the model is trained on fake data only (Faker and word lists from an open model on Featherless; no real or proving-ground value left the laptop); a word-list match is trusted without question; number formats (phone, national ID, licence plate) are not among its types; warnings do not stop a build.

### 2. PET per type, selected by the tool

`python -m pets_transformer.cli select --scenario HEALTH-S1` writes a contract itself. Every column gets a menu of candidate PETs (privacy-enhancing techniques) for its detected type; the order of the menu means nothing. The selector measures every candidate twice:

- Utility: the scores of the required tasks, measured with the organisers' utility code. A candidate is feasible when every required task stays within 0.05 (TOL) of a release with exact values.
- Risk: on the column's own table before the k repair, with the choices already made in place and every column not yet judged dropped, the share of rows whose combination of knowable values is shared by fewer than 5 rows. Knowable columns: every kept column the detector labels quasi-identifier (any subtype), plus every kept plain value of subtype CATEGORY with at most 20 distinct values. Sensitive attributes (diagnosis codes, vitals) are what an attacker wants, never what the attacker holds; dropped columns, keyed tokens and free text are out. No catalogue file and no attacker file is read.

The rule: among the feasible candidates with risk below the line (RISK_LINE 0.05, a policy number set by the team), the one with the highest mean utility; ties within 1e-9 go to the lower risk, then to fewer distinct values in the protected column (drop counts as 0, so a tie never keeps a finer value by accident), then to the candidate name in alphabetical order. If no feasible candidate is under the line, the feasible one with the lowest risk, and the reason says the line was not met. If none is feasible, the one with the best scores, and the reason says so. A column must earn its place: a candidate other than drop competes only if it raises at least one required task by MIN_GAIN (0.01) over drop, compared per task, and when none does, drop is chosen (the same holds in the repair pass); the gain test applies only when drop itself is feasible, since a drop that breaks a required task is no option. Risk is measured before the k repair; utility is measured after it in a second (repair) pass, which judges every quasi-identifier again, kept or dropped, by the same rule on the release after the k repair, where feasible means a mean score no worse than the current choice, so the selector never keeps a column so fine that the repair wipes it out (at most 3 rounds). The reason in each contract line lists every candidate with its utility scores and its risk, the line, and the risk after the k repair on the table's knowable columns ("line not met after repair" when it is still above). The contract's `fitness` block reports, with the scenario's trust level, the same count when the attacker knows every kept value except keyed tokens and free text; it decides nothing in selection. Evidence: `results/selection/HEALTH-S1.json` (v1, written by the earlier ladder selector, which kept the most private candidate that kept the tasks) and `results/selection/HEALTH-S1.v2.json` (v2, this rule).

| Column | Detected type | Candidates tried | Chosen |
|---|---|---|---|
| ed_visits.arrival_ts | quasi-identifier, timestamp | drop, month, ISO week (H-U8 0.0 each), hour of day (H-U8 1.0) | hour of day |
| ed_visits.date_of_birth | quasi-identifier, birth date | drop, 20-year band, 10-year band | 10-year band (also written to `age`) |
| ed_visits.municipality | quasi-identifier, municipality | drop, 8 most common else "other", exact | 8 most common |
| ed_visits.visit_id, lab_results.visit_id | identifier codes | drop, keyed token | keyed token (the visit-to-lab join needs it) |
| ed_visits.sex, vital signs, icd10_secondary, disposition | quasi-identifier, sensitive and plain values | drop, keep | drop (no required task needs them) |
| ed_visits.icd10_primary, triage, temp_c, los_minutes, readmit_30d | sensitive and plain values | drop, keep | keep |
| patient_hetu, patient_name, phone, home_address, chief_complaint | direct identifiers, free text | drop only | drop |
| clinical_notes, published_weekly_stats | whole tables | withhold | withheld (no task loses without them) |

The table above is the shipped `contracts/HEALTH-S1.json`, the selector v2 output: the same picks as the earlier ladder selector, new reasons and a `fitness` block. On HEALTH-S1 the line changed no choice: it did real work on arrival_ts only, where date and hour was feasible at risk 0.999 and hour of day (0.0227) is under the line, and even there it landed on v1's pick. The reasons of the knowable columns and of the columns judged after triage say "line not met". The menus by type: a timestamp tries drop, month, ISO week, hour of day, date, date and hour; a birth date drop, 20-year band, 10-year band; a place drop, 8 most common else "other", exact; coordinates drop, 2-decimal grid (about 1 km), 3-decimal grid (about 100 m); a postcode drop, 2 digits, 3 digits; an identifier code drop, keyed token. A contract can also replace two timestamps by the time between them (the `duration` PET), which a reviewer used for PUB-S3.

A quasi-identifier identifies someone only in combination, such as age band plus municipality. A token is a stand-in code: the same value always gets the same token, and without the secret key the token cannot be turned back into the value or put in order. The hand-written contract the team started from is kept as `contracts/HEALTH-S1.handwritten.json`; the selector drops more (sex, all vital signs but temperature, disposition); `results/health-s1-handwritten-build/` scores the hand-written one.

### 3. Protected output

`python -m pets_transformer.cli build --scenario HEALTH-S1` writes the protected `ed_visits.csv` and `lab_results.csv` with their row maps into `pets_submission/health/`, in a random row order, and only when the red-team gate and the utility check pass. No data file is committed: the folder is gitignored except the two label files. `ed_visits` keeps all 46398 rows (`results/health-s1-build/repair_report.json`). The organisers' identifier scan found no residual direct identifiers in the 7 files it scanned (`results/health-s1-build/check.txt`).

### 4. Utility before and after

| Task | What it measures | Raw | Main at 7cf541b | This release |
|---|---|---|---|---|
| H-U2 | Median length of stay by triage level | 1.0 | 1.0 | 0.9979 |
| H-U4 | Diagnosis-group mix in the eight largest municipalities | 1.0 | 1.0 | 0.9549 |
| H-U6 | 30-day revisit rate by age band | 1.0 | 0.9642 | 0.9578 |
| H-U7 | CRP vs temperature and CRP by diagnosis group | 1.0 | 1.0 | 1.0 |
| H-U8 | Hour-of-day arrival curve | 1.0 | 1.0 | 0.9446 |
| Privacy | 1 minus (half the worst risk plus half the mean risk) | 0.1716 | 0.9533 | 1.0 |
| Utility | Mean of the five task scores | 1.0 | 0.9928 | 0.971 |
| Composite | Weighted harmonic mean, privacy weight 30, utility weight 25 | 0.2752 | 0.9709 | 0.9866 |

Raw: `baseline-scores/health_HEALTH-S1_research-env_raw.json`. Main at 7cf541b: `results/health-s1-build/scorecard.json` at that commit. This release: `results/health-s1-build/scorecard.json`. For comparison, the organisers' B2-k baseline reaches utility 0.40 on HEALTH-S1 (`data/proving-ground/docs/BENCHMARK.md`, in the restored proving ground).

### 5. The scenario, the red team and residual risk

HEALTH-S1: a hospital gives its emergency-department visits and lab results to a university research group in a research environment. The group studies crowding and revisits, so the five tasks above must still work (`contracts/HEALTH-S1.json`).

**Our red team broke the earlier release, which the scorecard rated 0.9709** (`results/redteam/before-7cf541b.json`; attacks explained in `results/redteam/README.md`):

| Attack the scorecard does not run | Main at 7cf541b | This release | Gate |
|---|---|---|---|
| Order attack: share of rows whose dropped date is rebuilt from row order, `visit_id` or `lab_id` | 1.0 | 0.0002 | at most 0.05 |
| News-clip linkage with rebuilt dates: share of the 220 clips that name the right patient | 0.0455 (10 clips) | 0.0 | 0 |
| Person fingerprint: share of patients unique by their quasi-identifiers and set of arrival hours | 0.3544 | not applicable (no person key) | at most 0.05 |
| The organisers' linkage attacker, rerun with the age read from the band | 0.0 | 0.0 | at most 0.01 |
| Plain hashes reversible by dictionary | 0.0 | 0.0 | 0 |

Source for this release: `results/health-s1-build/redteam.json`. The gate runs in every build, as one function (`evaluate` in `src/pets_transformer/redteam.py`) before anything is copied, and every limit it reads comes from the scenario's signed policy (`policy/HEALTH-S1.policy.json`). It refuses the release, lists every reason and leaves `pets_submission/` unwritten when any of these holds:

- An attack is over its threshold, or should have run and could not. Each attack reports pass, fail or not applicable with a reason. Not applicable is allowed only when the release gives the attack nothing to work on: no hour-only column, no person key, no attacker quasi-identifier left.
- The scorer's minimum k on the contract's k-target table is under the target, the minimum k over the joined tables is under it (on the k columns; the count that includes the exact diagnosis code stays a reported number, see `docs/guarantee-and-residual-risk.md`), or the fewest distinct sensitive values in a group is under l.
- A check the contract's k target needs did not run in this build. The gate reads only what this run produced, never a file left in a reused `results/` folder.
- A task the scenario definition or the policy requires is missing from the scorecard or under the policy's floor, 0.5.
- The identifier scan found anything or did not run, or the scorecard's direct-identifier or free-text leakage risk is above zero.
- The protected folder holds a CSV the contract does not name, or lacks one it does. Only the released tables and their row maps are copied.

Keeping the patient pseudonym the organisers suggest fails it: 0.2935 of patients are unique by fingerprint (`results/health-s1-pseudonym-build/redteam.json`).

**The repair.** After protection, 3746 rows (0.0807) were in a group with k<5 or fewer than 2 distinct diagnoses, counting whether a visit has lab results as part of the group because the release shows it. Only those rows were coarsened, one step at a time: 3746 to a 20-year age band, 2584 still at risk to a 3-hour arrival block written as a range ("06:00 to 08:59", so nobody reads it as an exact hour), 737 to municipality "other", 59 suppressed, none dropped (`results/health-s1-build/repair_report.json`). The order of the steps was picked by scoring all 6 orders (`results/health-s1-build/repair_search.md`). Now every row has k of at least 5 (min k 5, median 55, `results/health-s1-build/scorecard.json`), every group at least 2 distinct diagnoses (`results/health-s1-build/checks/l_diversity.json`), and every visit with lab results shares its group with at least 4 others that have lab results (`results/health-s1-build/checks/joined_k.json`).

**Other scenarios, no hand-written rules.** The same build writes its own contract when none is reviewed yet: HEALTH-S3 (an AI vendor; composite 1.0 against 0.2769 raw, `results/health-s3-build/`), EDU-S2 (an edtech vendor; 0.9983 against 0.3395, `results/edu-s2-build/`), and ENERGY-S3 (energy-poverty research on 1.6 million hourly meter readings; 1.0 against 0.3506, `results/energy-s3-build/`). PUB-S3 is refused by the utility check: with a reviewer's edit that releases the time to resolution instead of two timestamps (`contracts/PUB-S3.json`), its research question scores 0.9767, but the area counts (0.3888) and the 1 km hotspot map (0.2987) cannot both survive k of at least 5 in one row-level table (`results/pub-s3-build/`).

**Every build.** All from the same code; `results/<name>-build/` holds each scorecard and gate.

| Build | Contract | Privacy | Utility | Composite | Gate |
|---|---|---|---|---|---|
| health-s1 | `contracts/HEALTH-S1.json` (selector) | 1.0 | 0.971 | 0.9866 | pass |
| health-s1-noflag | without the lab join flag | 1.0 | 0.9826 | 0.992 | pass |
| health-s1-informed | also closes the informed attacker | 1.0 | 0.9255 | 0.9647 | pass |
| health-s1-handwritten | the team's hand-written start | 1.0 | 0.9734 | 0.9877 | pass |
| health-s1-pseudonym | with the organisers' suggested patient key | 1.0 | 0.971 | 0.9866 | fail (fingerprint 0.2935) |
| health-s3 | selector | 1.0 | 1.0 | 1.0 | pass |
| edu-s2 | selector | 1.0 | 0.9963 | 0.9983 | pass |
| energy-s3 | selector | 1.0 | 1.0 | 1.0 | pass |
| pub-s3-auto | selector | 1.0 | 0.2131 | 0.3734 | fail (utility) |
| pub-s3 | selector, then reviewed | 1.0 | 0.5547 | 0.7327 | fail (utility) |

**Open for the team** (details and costs in `plans/2026-11-07-release-gate.md`): keep the lab join flag (0.9866, every visit with labs in a group of at least 5 such visits) or drop it (0.992, 0.055 of those visits in smaller groups, `results/health-s1-noflag-build/checks/joined_k.json`); ship the informed contract for a less trusted recipient; the gate thresholds are our choice. The hand-written contract scores 0.0011 higher than the selected one but leaves 0.121 of visits with labs in groups of fewer than 5 and lets the informed attacker single out 0.1599 of visits (`results/health-s1-handwritten-build/checks/`).

**Residual risk** (`docs/guarantee-and-residual-risk.md`): an attacker who already knows a visit's diagnosis group, age band, municipality and arrival hour singles out one row for 0.0971 of the visits, 0.9294 of them correctly (`results/health-s1-build/checks/informed_attacker.json`), and sees that visit's length of stay, temperature and lab values. `contracts/HEALTH-S1-informed.json` closes this (0.0) at composite 0.9647 (`results/health-s1-informed-build/`); the default relies on the research environment and the agreement with a known recipient instead. Neither is fit for public release.

## Demo video sequence

`demo/the-er-register.html` is the visual for the video. Open it in a browser, press Play and screen-record the 16:9 stage (about 16 seconds). It shows, on a sheet of 13 made-up patient records in the shape of the synthetic export: every field labelled, identifiers removed and the rest coarsened (birth date to age band, arrival to the hour, visit number to a keyed token), the rows shuffled, the release stamp, the fold, the address stamp and postmark, and the send-off. The figures it shows come from committed results: 46,398 visits and 3,746 coarsened (`results/health-s1-build/repair_report.json`), privacy 1.0 and utility 0.971 (`results/health-s1-build/scorecard.json`), 5 of 5 attacks failed (`results/health-s1-build/redteam.json`). `#autoplay` after the file name plays it on load; `#scrub=12000` freezes it at 12 seconds, for checking single frames. It needs no install; it loads the Newsreader and IBM Plex Mono fonts from Google Fonts and falls back to system fonts offline.

## How to run

Install once, from the repo root: create `.venv` at the repo root, install the organisers' `pets-eval` into it (`uv pip install --python .venv/bin/python -e data/proving-ground/toolkit`, see `context/pets-eval-howto.md`), then install this package into it with `uv pip install --python .venv/bin/python -e .`. The proving-ground data must be in place (`data/README.md`).

Optional, the column-type model: `uv pip install --python .venv/bin/python -e ".[semantic]"`, then download the encoder once (471 MB, the only network call): `.venv/bin/python -m pets_transformer.semantic.model --download`. With it installed, `detect` and `build` take `--semantic advisor` (the default when the model is present: word-list labels, model flags), `--semantic hybrid` (the model also labels what the word lists cannot place) or `--semantic lexicon` (word lists only; also set by `PETS_SEMANTIC=lexicon`). Without it, the default runs on the word lists and prints one warning; `--semantic advisor` or `hybrid` (or the same in `PETS_SEMANTIC`) stops with an error (`ModelUnavailable`) instead, and `build` records the mode that ran in `results/detect_mode.json`. Training and evaluation: `scripts/semantic/TRAINING.md` and `scripts/semantic/evaluate.py`.

One command does everything for the health scenario:

```
python -m pets_transformer.cli build --scenario HEALTH-S1
```

It needs a signed policy (see "Signing a policy" below) and refuses without one. It runs these steps: it verifies the policy's signature and refuses a contract the policy does not allow; the detector labels every column of the health tables and of the unseen HR export; if `contracts/<scenario>.json` does not exist, the selector writes a contract, which must come out with the hash the policy allows, to `contracts/generated/`; the repair search applies the contract with every order of the repair ladder and scores each; `protect` writes the release with the chosen order (tokens, shuffled rows, repair) under a fresh HMAC key; `score` runs the organisers' scorecard and identifier check against the raw baseline; `checks` and the red team run the attacks the scorecard does not run; only if the gate passes are the contract's files copied into `pets_submission/`, with a `release_record.json`. A scenario id works when `policy/` holds a signed policy for it: HEALTH-S1, HEALTH-S3, EDU-S2, ENERGY-S3 and PUB-S3 today. `--contract` builds from another contract file, but only one the policy allows: `contracts/HEALTH-S1.handwritten.json` and the no-flag and pseudonym variants are refused, and they stay as comparison evidence. `--policy-dir` reads the policy from another folder. A selected contract must match the signed hash byte for byte, and the selector's reasons quote measured scores, so one rounded digit is enough for a refusal: on the machine this was tested on, EDU-S2 re-selected with one such digit changed, while HEALTH-S3 matched. Pass the signed file instead: `build --scenario EDU-S2 --contract contracts/generated/EDU-S2.auto.json`. `python -m pets_transformer.cli select --scenario <id> --out <contract.json>` runs the selector alone; `python -m pets_transformer.cli redteam` runs the red team on any release, with the thresholds of the policy named by the contract's `scenario` key (it measures only, so it needs no signature); `python -m pets_transformer.cli checks --protected <release> --original <data> --contract <contract.json> --out <folder>` runs the three extra checks on any release whose contract has a k target. ENERGY-S3 (1.6 million meter readings) takes several minutes and a few GB of memory on a laptop. Options `--original`, `--out`, `--results`, `--submission` and `--pets-eval` override the defaults (the `pets-eval` default is `.venv/bin/pets-eval` at the repo root; the data default is `data/proving-ground`; the baseline is read from `baseline-scores/`).

What comes out:

- `results/health-s1-build/` (scorecards only, no labels): `scorecard.json` and `scorecard.html` (the organisers' scorecard), `check.txt` and `check.json` (identifier scan, the JSON is what the gate reads), `summary.md` (before and after per task and risk, k-anonymity, residual risk in plain words), `plan.md` (one row per column: detected role, PET, parameters, reason, and a note where a named rule overrides the detected role; tables not in the contract are listed as not released).
- `pets_submission/health/`: the protected tables and their row maps. Never committed, never published.
- `pets_submission/unseen_field_labels.csv` and `pets_submission/health_field_labels.csv`: the detector's labels for the unseen export and for the health tables. These are the only committed files in that folder.
- `results/health-s1-build/repair_search.md` and `repair_report.json`: every repair order scored, and how many rows each step changed. `results/health-s1-build/redteam.json`: the gate. `results/health-s1-build/checks/`: l-diversity, informed attacker, joined-table k (a build whose contract has no k target writes `checks/not_run.txt` instead). `selection.json`: the selector's evidence, when the build ran it. `results/redteam/before-7cf541b.json`: the gate on the earlier release.
- `out/health-s1-build/hmac.key`: the random key behind the tokens. Never committed.
- `release_record.json`, in `pets_submission/` and in `results/health-s1-build/`, only after a passing gate: the policy's sha256, the signature file name, the contract's sha256, the sha256 of every released file, the recipient, the purpose, the agreement reference, the recipient's duties, what is enforced after release (nothing, `enforced_after_release` is "none") and the residual risks from the checks. A refused rebuild removes the one in `results/`.

### Signing a policy

The data steward owns the limits. Each `policy/<scenario>.policy.json` needs a signature `policy/<scenario>.policy.json.sig`, and `policy/allowed_signers` lists the public key allowed to sign. The principal is `data-steward` and the namespace `pets-policy`; both are fixed in `src/pets_transformer/policy.py`, so a policy cannot name its own signer. The steward's private key stays on the steward's machine and never enters this repo; only the public key and the signatures are committed.

```
# once, on the steward's machine
ssh-keygen -t ed25519 -f ~/.ssh/pets-policy-steward
printf 'data-steward namespaces="pets-policy" %s\n' "$(cat ~/.ssh/pets-policy-steward.pub)" > policy/allowed_signers

# after every change to a policy file: remove the old signature first
rm -f policy/HEALTH-S1.policy.json.sig
ssh-keygen -Y sign -f ~/.ssh/pets-policy-steward -n pets-policy policy/HEALTH-S1.policy.json

# what build runs, to check by hand
ssh-keygen -Y verify -f policy/allowed_signers -I data-steward -n pets-policy -s policy/HEALTH-S1.policy.json.sig < policy/HEALTH-S1.policy.json
```

Remove the old `.sig` first: without a terminal to answer its overwrite prompt, `ssh-keygen -Y sign` exits 0 and keeps the old signature, and the build then refuses the policy.

What needs a new signature: any edit to a policy file. Editing a contract changes its sha256, so put the new hash in `allowed_contracts` (`shasum -a 256 contracts/HEALTH-S1.json`) and sign again. To build the informed contract, set `attacker_assumption` to `informed` in `policy/HEALTH-S1.policy.json`, sign, and run `build --scenario HEALTH-S1-informed`.

Where the numbers come from: every number is read from `scorecard.json`, written by the organisers' `pets-eval` (a self-assessment, not the official judging score). The "before" figures come from the committed raw baselines in `baseline-scores/`.

TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0).

## Rules we hold ourselves to

The rules live in `AGENTS.md` (data, claims, writing). Short version: synthetic or allowed data only, no privacy claim without method and parameters, every number from a committed scorecard, nothing from truth/, holdout/ or rowmap_*.csv in git or the zip.

## Attribution

TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0). The challenge is inspired by the European project TrustED (Horizon Europe grant agreement No. 101168467); this repository is not a TrustED deliverable.
