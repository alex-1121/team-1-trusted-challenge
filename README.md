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
| `decisions.md` | Team decision log |
| `AGENTS.md` | Rules for every teammate's coding agent |

## Rules we hold ourselves to

The rules live in `AGENTS.md` (data, claims, writing). Short version: synthetic or allowed data only, no privacy claim without method and parameters, every number from a committed scorecard, nothing from truth/, holdout/ or rowmap_*.csv in git or the zip.

## Attribution

TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0). The challenge is inspired by the European project TrustED (Horizon Europe grant agreement No. 101168467); this repository is not a TrustED deliverable.
