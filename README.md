# TrustED PETs Transformer

Since AI Hackathon 2026, Turku, 6-8 November. TrustED challenge: protect the data, keep its value.

## The challenge

We build a working tool that detects what each column and text field of a synthetic dataset contains. It picks a privacy-enhancing transformation (PET) per data type and sharing scenario, and transforms the data. Then it shows, with measured numbers, what risk was removed and what utility remains.

Status: Context pack landed 2026-11-06; dataset, scenario and demo shape are decided together on Friday night; spec and tickets follow in plans/.

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

`results/health-s1-build/plan.md` has one row per column: detected role, PET (privacy-enhancing technique), parameters and the reason. The reasons come from `contracts/HEALTH-S1.json`. One example per PET:

| Column | Detected role | PET | Reason (shortened) |
|---|---|---|---|
| ed_visits.patient_hetu | direct_identifier | pseudonym (keyed HMAC-SHA256) | Keeps patients linkable for the revisit task, blocks a dictionary attack on the national id |
| ed_visits.date_of_birth | quasi_identifier | age_band, width 10 | The scorer counts the band in k; also copied to `age` for the revisit-by-age task |
| ed_visits.municipality | quasi_identifier | top_n_exact_else_other, n 8 | Eight largest kept for the diagnosis-mix task, the rest become "other" to lift k |
| ed_visits.arrival_ts | quasi_identifier | hour_of_day | "HH:00" serves the arrival curve; date dropped, so no seasonality study |
| ed_visits.patient_name | direct_identifier | drop | No required task needs it |
| ed_visits.icd10_primary | sensitive_attribute | keep | The study needs the diagnosis code |
| clinical_notes (whole table) | free_text and others | withhold | Free text carries identifying detail; no task uses it, no redactor in scope |

A quasi-identifier is a column that identifies someone only in combination, such as age band plus municipality. k is the size of the smallest group of rows that share the same quasi-identifier values. A pseudonym is a stand-in code: the same national id always gets the same code, and without the secret key the code cannot be turned back into the id.

### 3. Protected output

`python -m pets_transformer.cli build --scenario HEALTH-S1` writes the protected `ed_visits.csv` and `lab_results.csv` with their row maps into `pets_submission/health/`. No data file is committed: the folder is gitignored except the two label files. `ed_visits` keeps all 46398 rows (`results/health-s1-build/scorecard.json`). The organisers' identifier scan found no residual direct identifiers in the 6 files it scanned (`results/health-s1-build/check.txt`). The video shows the folder live.

### 4. Utility before and after

| Task | What it measures | Before | After |
|---|---|---|---|
| H-U2 | Median length of stay by triage level | 1.0 | 1.0 |
| H-U4 | Diagnosis-group mix in the eight largest municipalities | 1.0 | 1.0 |
| H-U6 | 30-day revisit rate by age band | 1.0 | 0.9642 |
| H-U7 | CRP vs temperature and CRP by diagnosis group | 1.0 | 1.0 |
| H-U8 | Hour-of-day arrival curve | 1.0 | 1.0 |
| Privacy | 1 minus (half the worst risk plus half the mean risk) | 0.1716 | 0.9533 |
| Utility | Mean of the five task scores | 1.0 | 0.9928 |
| Composite | Weighted harmonic mean, privacy weight 30, utility weight 25 | 0.2752 | 0.9709 |

Before: `baseline-scores/health_HEALTH-S1_research-env_raw.json`. After: `results/health-s1-build/scorecard.json`, also in `results/health-s1-build/summary.md`. For comparison, the organisers' B2-k baseline reaches utility 0.40 on HEALTH-S1 (`data/proving-ground/docs/BENCHMARK.md`, in the restored proving ground).

### 5. The scenario and residual risk

HEALTH-S1: a hospital gives its emergency-department visits and lab results to a university research group in a research environment. The group studies crowding and revisits, so the five tasks above must still work (`contracts/HEALTH-S1.json`).

Residual risk, from `results/health-s1-build/summary.md`: in ed_visits, the share of records with k<5 is 0.0779. That means 7.8% of the records share their quasi-identifier combination with fewer than 5 rows, so an attacker who knows those attributes about a person can narrow the match to a handful of rows or one. The share is lower than in the earlier release because we dropped arrival_mode, the finding of the l-diversity check below. Attacker model: the toolkit's shipped attackers only. Attacks run: linkage re-identification with the shipped attacker files, a dictionary attack on hashed columns, a direct-identifier pattern scan, and k over the quasi-identifiers in the field catalogue. We did not test stronger attackers (more background knowledge, other outside data).

Checks the scorecard does not run (`python -m pets_transformer.cli checks`):

- l-diversity (how mixed the diagnoses, the sensitive attribute, are inside each group of rows that share the scorer's quasi-identifiers: age band, sex, municipality and arrival hour): 0.1128 of the groups have only one distinct diagnosis (`results/checks/l_diversity.json`). In the earlier release, which also kept arrival_mode, it was 0.2787 (`results/checks/l_diversity.json` at commit a7c9b76). That finding is why arrival_mode, which no task reads, is now dropped; every task score stayed the same and the scores in the table above are the release after the drop.
- An attacker who knows a visit's diagnosis group, age band, municipality and arrival hour singles out exactly one row for 0.1282 of the 46398 visits, always the right one, against 0.2501 with the same facts on the original tables (`results/checks/informed_attacker.json`). "Always the right one" holds by construction, because the facts come from the visit's own record. 0.1282 counts unique matches only: it is not an upper bound, since an attacker who guesses among a few matching rows, or also knows the patient's sex (kept in the release), can do better. We did not measure that.
- Joining ed_visits to lab_results and counting the diagnosis codes as part of the key, 0.9525 of the joined rows sit in groups of fewer than 5 visits; over the quasi-identifiers alone it is 0.1459 (`results/checks/joined_k.json`). k usually leaves diagnoses out; we report the 0.9525 because a researcher who knows a patient's exact diagnosis codes can use them to find the row.

What we guarantee and what we do not: `docs/guarantee-and-residual-risk.md`.

## How to run

Install once, from the repo root: create `.venv` at the repo root, install the organisers' `pets-eval` into it (`uv pip install --python .venv/bin/python -e data/proving-ground/toolkit`, see `context/pets-eval-howto.md`), then install this package into it with `uv pip install --python .venv/bin/python -e .`. The proving-ground data must be in place (`data/README.md`).

One command does everything for the health scenario:

```
python -m pets_transformer.cli build --scenario HEALTH-S1
```

It runs four steps: the detector labels every column of the health tables and of the unseen HR export; `protect` applies `contracts/HEALTH-S1.json` using those labels; `score` runs the organisers' scorecard and identifier check against the raw baseline; the result is assembled into `pets_submission/`. Options `--original`, `--out`, `--results`, `--submission` and `--pets-eval` override the defaults (the `pets-eval` default is `.venv/bin/pets-eval` at the repo root; the data default is `data/proving-ground`; the baseline is read from `baseline-scores/`).

What comes out:

- `results/health-s1-build/` (scorecards only, no labels): `scorecard.json` and `scorecard.html` (the organisers' scorecard), `check.txt` (identifier scan), `summary.md` (before and after per task and risk, k-anonymity, residual risk in plain words), `plan.md` (one row per column: detected role, PET, parameters, reason, and a note where a named rule overrides the detected role; tables not in the contract are listed as not released).
- `pets_submission/health/`: the protected tables and their row maps. Never committed, never published.
- `pets_submission/unseen_field_labels.csv` and `pets_submission/health_field_labels.csv`: the detector's labels for the unseen export and for the health tables. These are the only committed files in that folder.
- `out/health-s1-build/hmac.key`: the random key behind the pseudonyms. Never committed.

Where the numbers come from: every number is read from `scorecard.json`, written by the organisers' `pets-eval` (a self-assessment, not the official judging score). The "before" figures come from the committed raw baselines in `baseline-scores/`.

## What is where

| Path | What it holds |
|---|---|
| `contracts/` | One JSON contract per scenario: recipient, purpose, role rules (by detected role) and named column rules, each with a reason |
| `src/pets_transformer/` | The code: `detect`, `protect`, `score`, `build` and the command line |
| `results/` | Committed evidence: detector results, gate runs, and the output of each build |
| `pets_submission/` | What goes to the organisers on request; only the two label files are committed |

TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0).

## Rules we hold ourselves to

The rules live in `AGENTS.md` (data, claims, writing). Short version: synthetic or allowed data only, no privacy claim without method and parameters, every number from a committed scorecard, nothing from truth/, holdout/ or rowmap_*.csv in git or the zip.

## Attribution

TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0). The challenge is inspired by the European project TrustED (Horizon Europe grant agreement No. 101168467); this repository is not a TrustED deliverable.
