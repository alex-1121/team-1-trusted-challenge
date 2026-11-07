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

## How to run

Install once, from the repo root, into the existing virtual environment (`pip install -e .`). The organisers' `pets-eval` tool and the proving-ground data must be in place (`data/README.md`).

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
