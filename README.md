# TrustED PETs Transformer

Since AI Hackathon 2026, Turku, 6-8 November. TrustED challenge: protect the data, keep its value.

## The challenge

We build a working tool that detects what each column and text field of a synthetic dataset contains. It picks a privacy-enhancing transformation (PET) per data type and sharing scenario, and transforms the data. Then it shows, with measured numbers, what risk was removed and what utility remains.

Status (2026-11-07): HEALTH-S1 is the scored scenario; the build detects, protects, repairs, scores and red-teams in one command (`plans/2026-11-07-release-gate.md`).

## Start here

1. `context/README.md` - index of everything in this repo.
2. `context/challenge-digest.md` - the whole challenge in one page.
3. `team/plan.md` - schedule, roles, open questions.

## Layout

| Path | What it holds |
|---|---|
| `context/` | The official brief, one-pager, video transcript, source file list, challenge digest, and the organiser docs in `context/proving-ground/` |
| `team/` | Team plan and the submission checklist |
| `plans/` | Specs, tickets and plans (see `plans/README.md`) |
| `data/` | The proving-ground data, gitignored; `data/README.md` says how to restore it |
| `baseline-scores/` | "Before" scorecards: every original table scored unprotected, one HTML + JSON pair per scenario, named `<dataset>_<SCENARIO>_<recipient>_raw` |
| `attack_analysis.md` | What `pets-eval` actually measures: risk checks, utility tasks, how the score is aggregated, blind spots |
| `decisions.md` | Team decision log |
| `AGENTS.md` | Rules for every teammate's coding agent |

## The demo in five items

Every number below is copied from the file named after it in brackets. Scorecard numbers come from the organisers' `pets-eval`. They are our self-assessment and are separate from the official judging score.

### 1. Types found

The detector labels every column from its values alone; it never reads column names. It was tuned on six datasets and scored with `pets-eval detect` on three it did not see while tuning (`results/detect/SPLIT.md`).

| Held-out dataset | macro-F1 | accuracy | sensitive recall |
|---|---|---|---|
| health | 0.8086 (`results/detect/health.json`) | 0.717 (`results/detect/health.json`) | 0.7209 (`results/detect/health.json`) |
| public_admin | 0.7241 (`results/detect/public_admin.json`) | 0.8108 (`results/detect/public_admin.json`) | 0.8519 (`results/detect/public_admin.json`) |
| customer_service | 0.7821 (`results/detect/customer_service.json`) | 0.7692 (`results/detect/customer_service.json`) | 0.9565 (`results/detect/customer_service.json`) |

The target was macro-F1 above 0.65, the organisers' rule baseline B1 (`results/detect/SPLIT.md`). macro-F1 is the F1 score (a balance of missed and wrong labels) worked out per privacy role and then averaged, so rare roles count as much as common ones; 1.0 is perfect. One caveat: eight rules were added after reading public_admin's errors and the held-out label rows, so public_admin's 0.7241 and customer_service's 0.7821 are not clean held-out scores. Before those rules they were 0.5431 and 0.7462 (`results/detect/RESULTS.md`). The health score did not change (`results/detect/RESULTS.md`).

The same detector labelled the organisers' unlabelled HR export: 26 columns in `results/detect/unseen_field_labels.csv`, format `column,privacy_role,subtype`. The organisers hold the answers, so we have no score for it.

### 2. PET per type

`results/health-s1-build/plan.md` has one row per column: detected role, PET (privacy-enhancing technique), parameters and the reason, plus one row per repair step with the number of rows it changed. The reasons come from `contracts/HEALTH-S1.json`. One example per PET:

| Column | Detected role | PET | Reason (shortened) |
|---|---|---|---|
| ed_visits.visit_id, lab_results.visit_id, lab_results.lab_id | record_key, technical_identifier | token (keyed HMAC-SHA256) | Sequential keys give back the arrival order; the same token in both tables keeps the visit-to-lab join |
| ed_visits.patient_hetu | direct_identifier | drop | A pseudonym linked every visit into a fingerprint; H-U6 reads readmit_30d instead |
| ed_visits.date_of_birth | quasi_identifier | age_band, width 10 (20 on the rows at risk) | The scorer counts the band in k; also copied to `age` for the revisit-by-age task |
| ed_visits.municipality | quasi_identifier | top_n_exact_else_other, n 8 ("other" on the rows at risk) | Eight largest kept for the diagnosis-mix task |
| ed_visits.arrival_ts | quasi_identifier | hour_of_day (3-hour block on the rows at risk) | "HH:00" serves the arrival curve; date dropped |
| ed_visits.icd10_primary | sensitive_attribute | keep | The study needs the diagnosis code; every group holds at least 2 distinct codes |
| clinical_notes (whole table) | free_text and others | withhold | Free text carries identifying detail; no task uses it, no redactor in scope |

A quasi-identifier is a column that identifies someone only in combination, such as age band plus municipality. k is the size of the smallest group of rows that share the same quasi-identifier values; l is the number of distinct diagnoses in that group. A token is a stand-in code: the same value always gets the same token, and without the secret key the token cannot be turned back into the value or put in order.

### 3. Protected output

`python -m pets_transformer.cli build --scenario HEALTH-S1` writes the protected `ed_visits.csv` and `lab_results.csv` with their row maps into `pets_submission/health/`, in a random row order, and only when the red-team gate passes. No data file is committed: the folder is gitignored except the two label files. `ed_visits` keeps all 46398 rows (`results/health-s1-build/repair_report.json`). The organisers' identifier scan found no residual direct identifiers in the 7 files it scanned (`results/health-s1-build/check.txt`).

### 4. Utility before and after

| Task | What it measures | Raw | Main at 7cf541b | This release |
|---|---|---|---|---|
| H-U2 | Median length of stay by triage level | 1.0 | 1.0 | 1.0 |
| H-U4 | Diagnosis-group mix in the eight largest municipalities | 1.0 | 1.0 | 0.8744 |
| H-U6 | 30-day revisit rate by age band | 1.0 | 0.9642 | 0.9641 |
| H-U7 | CRP vs temperature and CRP by diagnosis group | 1.0 | 1.0 | 1.0 |
| H-U8 | Hour-of-day arrival curve | 1.0 | 1.0 | 0.9945 |
| Privacy | 1 minus (half the worst risk plus half the mean risk) | 0.1716 | 0.9533 | 1.0 |
| Utility | Mean of the five task scores | 1.0 | 0.9928 | 0.9666 |
| Composite | Weighted harmonic mean, privacy weight 30, utility weight 25 | 0.2752 | 0.9709 | 0.9845 |

Raw: `baseline-scores/health_HEALTH-S1_research-env_raw.json`. Main at 7cf541b: `results/health-s1-build/scorecard.json` at that commit. This release: `results/health-s1-build/scorecard.json`. For comparison, the organisers' B2-k baseline reaches utility 0.40 on HEALTH-S1 (`data/proving-ground/docs/BENCHMARK.md`, in the restored proving ground).

### 5. The scenario, the red team and residual risk

HEALTH-S1: a hospital gives its emergency-department visits and lab results to a university research group in a research environment. The group studies crowding and revisits, so the five tasks above must still work (`contracts/HEALTH-S1.json`).

**Our red team broke the earlier release, which the scorecard rated 0.9709** (`results/redteam/before-7cf541b.json`):

| Attack the scorecard does not run | Main at 7cf541b | This release | Gate |
|---|---|---|---|
| Order attack: share of rows whose dropped date is rebuilt from row order, `visit_id` or `lab_id` | 1.0 | 0.0002 | at most 0.05 |
| News-clip linkage with rebuilt dates: share of the 220 clips that name the right patient | 0.0455 (10 clips) | 0.0 | 0 |
| Person fingerprint: share of patients unique by age band, sex, municipality and their set of arrival hours | 0.3544 | not applicable (no person key) | at most 0.05 |

Source for this release: `results/redteam/after.json`. The gate runs in every build; when an attack passes its threshold, the build stops and `pets_submission/` is not written.

**The repair.** After the fixes, 3613 rows (0.0779) were still in a group with k<5 or l<2. Only those were coarsened, one step at a time, re-measuring after each step; the order of the steps was picked by scoring all 6 orders (`results/health-s1-build/repair_search.md`). Now every row has k of at least 5 and every group at least 2 distinct diagnoses (`results/health-s1-build/scorecard.json`, `results/checks/l_diversity.json`). A global setting cannot do this: 20-year bands for every row drop H-U6 to 0.0271 (`results/sweep/sweep.md`), while 20-year bands on the 3613 rows at risk keep it at 0.9641.

**Residual risk** (`docs/guarantee-and-residual-risk.md`): an attacker who already knows a visit's diagnosis group, age band, municipality and arrival hour singles out one row for 0.0981 of the visits, 0.9292 of them correctly (`results/checks/informed_attacker.json`), and sees that visit's clinical values. Joined with lab results and keyed on exact diagnosis codes, 0.9521 of joined rows sit in groups of fewer than 5 visits (`results/checks/joined_k.json`). The release relies on the research environment and the agreement with a known recipient; it is not fit for public release.

## How to run

Install once, from the repo root: create `.venv` at the repo root, install the organisers' `pets-eval` into it (`uv pip install --python .venv/bin/python -e data/proving-ground/toolkit`, see `context/pets-eval-howto.md`), then install this package into it with `uv pip install --python .venv/bin/python -e .`. The proving-ground data must be in place (`data/README.md`).

One command does everything for the health scenario:

```
python -m pets_transformer.cli build --scenario HEALTH-S1
```

It runs these steps: the detector labels every column of the health tables and of the unseen HR export; the repair search applies `contracts/HEALTH-S1.json` with every order of the repair ladder and scores each; `protect` writes the release with the chosen order (tokens, shuffled rows, repair); `score` runs the organisers' scorecard and identifier check against the raw baseline; `checks` and the red team run the attacks the scorecard does not run; only if the red-team gate passes is the result assembled into `pets_submission/`. `python -m pets_transformer.cli redteam` runs the red team on any release. Options `--original`, `--out`, `--results`, `--submission` and `--pets-eval` override the defaults (the `pets-eval` default is `.venv/bin/pets-eval` at the repo root; the data default is `data/proving-ground`; the baseline is read from `baseline-scores/`).

What comes out:

- `results/health-s1-build/` (scorecards only, no labels): `scorecard.json` and `scorecard.html` (the organisers' scorecard), `check.txt` (identifier scan), `summary.md` (before and after per task and risk, k-anonymity, residual risk in plain words), `plan.md` (one row per column: detected role, PET, parameters, reason, and a note where a named rule overrides the detected role; tables not in the contract are listed as not released).
- `pets_submission/health/`: the protected tables and their row maps. Never committed, never published.
- `pets_submission/unseen_field_labels.csv` and `pets_submission/health_field_labels.csv`: the detector's labels for the unseen export and for the health tables. These are the only committed files in that folder.
- `results/health-s1-build/repair_search.md` and `repair_report.json`: every repair order scored, and how many rows each step changed. `results/redteam/`: the red-team gate before (main at 7cf541b) and after.
- `out/health-s1-build/hmac.key`: the random key behind the tokens. Never committed.

Where the numbers come from: every number is read from `scorecard.json`, written by the organisers' `pets-eval` (a self-assessment, not the official judging score). The "before" figures come from the committed raw baselines in `baseline-scores/`.

## What is where

| Path | What it holds |
|---|---|
| `contracts/` | One JSON contract per scenario: recipient, purpose, role rules (by detected role) and named column rules, each with a reason |
| `src/pets_transformer/` | The code: `detect`, `protect`, `repair`, `score`, `checks`, `redteam`, `build` and the command line |
| `results/` | Committed evidence: detector results, gate runs, and the output of each build |
| `pets_submission/` | What goes to the organisers on request; only the two label files are committed |

TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0).

## Rules we hold ourselves to

The rules live in `AGENTS.md` (data, claims, writing). Short version: synthetic or allowed data only, no privacy claim without method and parameters, every number from a committed scorecard, nothing from truth/, holdout/ or rowmap_*.csv in git or the zip.

## Attribution

TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0). The challenge is inspired by the European project TrustED (Horizon Europe grant agreement No. 101168467); this repository is not a TrustED deliverable.
