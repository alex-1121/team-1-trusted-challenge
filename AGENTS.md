# AGENTS.md

Instructions for every coding agent working in this repository. Humans: read `README.md` first.

## What this is

The team build for the TrustED PETs Transformer challenge at Since AI Hackathon 2026 (Turku, 6-8 November). Detect sensitive data types in synthetic datasets, apply a privacy-enhancing transformation per type and sharing scenario, and show with measured numbers what risk was removed and what utility remains. Read `context/README.md` before doing anything else; `context/challenge-digest.md` is the challenge in one page.

## Data rules

- `data/proving-ground/` is gitignored. Never commit a CSV, parquet or any file from it. `data/README.md` says how to restore it.
- `rowmap_*.csv` are never published anywhere (organiser rule). `truth/` and `holdout/` are never committed and never go into the submission zip (team rule: they are the answer key to the attacks).
- Read every CSV with `dtype=str` first; phone numbers, postcodes and identifiers break when parsed as numbers.
- Only the synthetic proving-ground data, public data, or data we are explicitly allowed to use.

## Claim rules

- Never write "anonymised", "GDPR compliant" or "differentially private" without the method and its parameters next to it.
- Every number in a slide, video, README or submission text comes from a scorecard run whose JSON is committed. No invented metrics.
- Attribution for anything we publish: "TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0)".

## Licences and people

- The proving ground is CC BY 4.0 (data) and MIT (code), (c) 2026 Since AI ry. Attribution line: "TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0)".
- The brief, one-pager and video are organiser materials, redistributed for the team only.
- The licence for our own code is an open decision (row in `decisions.md`).

## Writing rules

- No em-dash. Use " - ".
- Verbatim organiser files (context/brief.md, context/brief-onepager.md, context/video-transcript.md, everything under context/proving-ground/ and context/originals/) keep their own text, em-dashes included.
- Plain English, short sentences. Explain a term the first time it appears.
- No secrets, tokens or real personal data in any file. The repo goes public for the submission.

## Where things go

- Plans and notes: `plans/`, one markdown per plan, see `plans/README.md`.
- Decisions: a row in `decisions.md`.
- Context you discover about the challenge or the data: `context/`, with a "Source:" line.
- Project index: the "Layout" table in `README.md` has one row per top-level file and folder. When you add, rename, move or delete one, update its row in the same commit. Files inside `context/` and `team/` are indexed in `context/README.md` instead; update that file when you change one of them.
