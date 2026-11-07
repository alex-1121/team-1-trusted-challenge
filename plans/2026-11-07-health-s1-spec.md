# Spec: HEALTH-S1 PETs Transformer (research-environment release of the ED data)

Status: proposed. Author: Claude Fable 5.1, run by Arda, 2026-11-07, from the decision row of 2026-11-07, the review at the end of `2026-11-06-build-idea-candidates.md`, and the gate run in `../results/health-s1-gate/GATE.md`. Comment as PR review comments or inline `> note (name):` lines. No interview was run (the build is unattended), so every choice below is open to the team.

## TL;DR

We build one tool that reads the health tables, works out what each column is from its values, applies one protection per column according to a written contract for scenario HEALTH-S1 (a university research group studying ED crowding and revisits), writes the protected tables, and scores before and after with the organisers' toolkit. The gate run already showed the design that keeps the hour-of-day task alive while removing the direct identifiers; the tool turns that hand-made copy into a repeatable, explained program, and the same detector labels the organisers' unlabelled `unseen` export.

## Problem statement

A hospital wants to give a research group its emergency-department visits and lab results so they can study length of stay, revisits, diagnosis mix and arrival patterns. The raw tables carry personal identity codes, birth dates, postcodes, exact arrival times and free text. Handing them over as they are re-identifies patients; blanking everything kills the research. Today the choice is made by hand, column by column, with no written reason and no number that says how much risk was removed and how much value remains.

## Solution

A command-line tool with three verbs. `detect` labels every column of a dataset from its values alone (role and subtype in the organisers' vocabulary). `protect` reads a scenario contract (who receives the data, for what, against which attacker, which analyses must still work) and the detected labels, picks one privacy-enhancing technique (PET) per column with a one-line reason tied to the scenario, writes the protected tables plus the row maps the scorer needs, and prints the choice table. `score` runs the organisers' scorecard on the original and the protected folder and writes a before-and-after summary with the residual risks in plain words. The health release for HEALTH-S1 is the scored story; the `unseen` export is labelled by the same detector.

## User stories

1. As the research group, I want the hour-of-day arrival curve, length of stay by triage level, diagnosis mix in the eight largest municipalities, 30-day revisit rate by age band, and CRP versus temperature, so that my study works on the protected data.
2. As the research group, I want a stable patient pseudonym and a working visit-to-lab join, so that revisit and lab analyses still link.
3. As the hospital's data steward, I want no direct identifier left in the release, so that no row names a patient.
4. As the data steward, I want every quasi-identifier generalised so that at least 5 rows share each combination of the scored columns, so that record linkage against the public directory fails.
5. As the data steward, I want a table that says, per column, what was done and why for this recipient, so that I can defend the release.
6. As the data steward, I want to see which columns were withheld and why, so that the omission is a stated choice.
7. As the team, I want the tool to label columns from values alone, so that it works on a dataset nobody annotated.
8. As the team, I want the detector scored on a dataset it never saw, so that the score means something.
9. As the team, I want one command that produces the protected folder, the row maps and the scorecard, so that a rerun after a change takes minutes.
10. As the team, I want every number in the deck and video copied from a committed scorecard JSON, so that no claim is invented.
11. As the team, I want the privacy claim stated with its method and parameters (keyed HMAC pseudonym, k at least 5 on the named columns, hour-of-day only), so that nobody writes "anonymised".
12. As the team, I want the residual risks printed from the scorecard components, so that the limitations slide is honest.
13. As the judges, I want to see the five demo items (types found, PET per type, protected output, utility before and after, the scenario) in one flow.
14. As the organisers, I want `pets_submission/unseen_field_labels.csv` in the format `column,privacy_role,subtype`, so that the hidden detection check can run.
15. As the organisers, I want protected health tables with row maps in `pets_submission/health/`, so that the hidden attacker can be run, handed over without publishing the row maps.
16. As a teammate, I want a small joint sweep (age band width, k target) scored by the scorecard, so that the chosen parameters are shown, not guessed.
17. As a teammate, I want `pets-eval check` to pass on the output folder, so that no identifier pattern leaked.
18. As the data steward, I want k computed by our own tool over the columns the scenario names (age band, sex, municipality, arrival hour), not only the scorer's set, so that the stated guarantee covers age.

## Implementation decisions

- One Python package in this repo, installed into the existing `.venv`, with a CLI exposing `detect`, `protect` and `score`. Plain pandas, no new heavy dependency.
- The scenario contract is a small YAML or JSON file per scenario holding: recipient, purpose, trust level, threat model, required utility tasks, and a per-column resolution (keep, generalise with parameters, pseudonymise, drop, withhold table) with a reason that names the task or attacker it serves. The HEALTH-S1 contract is written by hand from the gate design; it is the single source for the choice table.
- Time design for `arrival_ts`: hour of day only as "HH:00", date dropped. The gate run proved it on the first attempt (H-U8 1.0, k<5 share 0.0094, privacy 0.9944, utility 0.9928, composite 0.9937 against B0 0.2752), see `../results/health-s1-gate/GATE.md`. The price: no seasonality study is possible on the release; the contract states it.
- Patient key: keyed HMAC-SHA256 pseudonym, same key for every table in one run, key generated per run and never committed; column names unchanged so the toolkit's consistency check and the join still find them. A plain hash is forbidden (the toolkit's dictionary attack reverses it).
- Age: 10-year bands by default, width a sweep parameter; `dob` dropped. Municipality: the eight most frequent kept exact, the rest "other". Dropped from `ed_visits`: `discharge_ts`, `ambulance_unit`, `postcode`, `dob`, `chief_complaint`. Dropped from `lab_results`: `sampled_ts`. Withheld tables: `clinical_notes`, `published_weekly_stats`. Every one of these is a contract line with its reason.
- The detector is a rule-and-feature classifier over column values: pattern matchers for the identifier subtypes (national id, IBAN, phone, email, postcode, plate, device ids, hashes), value statistics (cardinality ratio, numeric range, date parse rate, text length) for roles, and a small lexicon for names, municipalities and diagnosis codes drawn only from the proving-ground data. It is tuned on a subset of the nine catalogued datasets and evaluated with `pets-eval detect` on the held-out datasets; catalog-on-catalog is not a result. It writes one labels file per dataset in the detect format and `unseen_field_labels.csv` for the HR export.
- `protect` applies the contract by column role where the contract says so (for example "every direct_identifier is dropped unless named as the pseudonym key") and by column name where the contract names a column, so the detector's labels and the contract meet in one plan table: column, detected role, PET, parameters, reason.
- `score` wraps the toolkit's scorecard and check commands, stores JSON and HTML under `results/`, and writes a markdown summary: per-task utility before (the committed B0 scorecard) and after, each privacy risk component, the k summary, and a residual-risk paragraph generated from the components in plain words.
- The sweep varies only age band width and the k target, scores each cell with the scorecard, and records a table; the chosen cell is the one with the best composite subject to every required task above a stated floor.
- `pets_submission/` is built by one command: `health/` protected tables with row maps, `unseen_field_labels.csv`. The folder is gitignored except the labels file. How to hand it to the organisers is open (Discord).

## Testing decisions

- Tests exercise external behaviour at the CLI and the plan table, not internals: given a tiny synthetic frame and a contract, the protected frame has the expected columns, every pseudonym repeats for the same patient, no original identifier value survives, the plan table has one row per original column.
- The detector's acceptance test is the `pets-eval detect` score on the held-out datasets (target: macro-F1 above the organisers' rule baseline B1, 0.65), recorded in `results/`.
- The end-to-end acceptance is one scorecard run per change, committed as JSON; H-U2, H-U4, H-U6, H-U7, H-U8 all above zero, the k<5 share at or below the gate run, no direct identifier retained, `pets-eval check` clean.
- Prior art: `data/proving-ground/toolkit/tests/` and `examples/quickstart.py`.

## Out of scope

A natural-language request interpreter; an LLM choosing PETs; a learned PET selector; a per-PET-per-column grid benchmark; HEALTH-S3 as a built second story; a clinical-notes redactor for S1 (the table is withheld); differential privacy (no S1 task needs it); any dataset beyond health for protection (the detector alone runs on all).

## Further notes

- Rules in `../AGENTS.md` bind every ticket: dtype=str reads, no em-dash, no data files or row maps in git, every published number from a committed scorecard JSON, attribution line on anything published.
- The before numbers are the committed B0 scorecard in `../baseline-scores/health_HEALTH-S1_research-env_raw.json` (privacy 0.1716, utility 1.0, composite 0.2752). The organisers' B2-k reached utility 0.40 on HEALTH-S1 by rounding the arrival time; the gate design exists to beat that.
- Scope freeze Saturday 18:00; video, deck and submission before Sunday 10:00 Turku time.
