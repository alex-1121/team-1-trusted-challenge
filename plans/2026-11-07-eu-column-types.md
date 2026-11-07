# Plan: tell what a column holds in any EU language - word lists first, a model for the rest

Status: proposed. Author: Claude Opus 5.5, run by zray, 2026-11-07 15:45 Turku time. Comment inline as `> note (name):` lines. Numbers marked "scratch run" come from an experiment outside the repo and are not citable until the work below commits them (AGENTS.md).

## TL;DR

Our detector finds names, towns, sex, occupations, languages and company names by looking values up in word lists built from the Finnish proving ground. On data from other EU countries those lookups find nothing and the column is labelled harmless.

We add a small model that reads a sample of a column's values and returns a probability for each data type, calibrated so that "0.8" means right about 8 times in 10. Both run on every column:

- **The word list finds a match:** its label stands, as today.
- **The word list finds nothing:** the model's label is used.
- **They disagree in a way that would change the PET** (privacy-enhancing technique), and the model gives the word list's answer little chance: the tool prints a warning and lists the column for a person to look at. It does not stop the build.

The aim is as much automation as possible, with warnings where a person's look is worth it. Everything after detection stays as it is. For the hackathon the aim is the right idea and plan, shown working end to end with honest numbers; a better-trained model and bigger word lists come later. The work happens on a fork, so the word-list version on `main` stays the one we present if this is not ready by Sunday 08:00.

## Why

- The brief asks us to show "the data types identified in the original dataset" (`context/brief.md`, section 03). Headers cannot be trusted. The organisers hide them on purpose in the unseen HR export (`c01..c26`, `data/proving-ground/data/unseen/README.md`), and in real exports they can be missing, abbreviated or wrong. Choosing a PET from a wrong type is the most expensive mistake the tool can make, so the type must come from the values.
- A product for an EU project will get health data from several countries. Scratch run on fake customer tables for 8 countries (FI, DE, FR, PL, IT, ES, NL, SE; 22 columns each, Faker):
  - our rules labelled first, last and full names harmless in 6 of 8 countries;
  - towns harmless in all 8 (even Finland, because the fake Finnish towns are not in our 28-town list);
  - sex harmless outside Finland ("weiblich", "kobieta" are not in our list);
  - 61 of 176 risky columns ended up as non_sensitive.
- A bigger word list does not fix this alone. It never covers every spelling, it cannot settle "Jordan" (name or country) or "Paris" (name or city), and it knows nothing about the column as a whole. In the same scratch run, Presidio's name finder, a trained model rather than a list, found names in all 8 countries.
- Presidio itself is not the answer as a column detector. On the proving ground it scored macro-F1 0.37 against our rules' 0.81 on the three held-out datasets (scratch run), because it has no idea of record keys, categories or table context.
- Keeping the word lists first means the Finnish proving-ground results, which already work, barely move. The model adds the cases the lists cannot reach, and the disagreement check also catches a list matching the wrong thing.

## Decisions by zray (2026-11-07)

- A word-list match is trusted. The model labels what the lists cannot match.
- Every column is checked by both. A disagreement that would change the PET, with low model confidence for the word list's answer, gives a warning and a request for a person to look.
- A column needing review **prints a warning; the build goes on.** Automation is the point of the challenge, so some risk is accepted.
- Work on a fork; announce it on `main`; present the word-list version if the work is not ready in time.
- Training and cloud tools are the author's call (section "Tools").

## Goals

1. Detect these types from values alone, in any EU language, without needing a list for that language: person name, street address, town or municipality, other place name (region, country), organisation name, occupation, language, sex, free text, and "harmless category" as the contrast class.
2. Each column the model sees gets a calibrated probability per type, a decision and a one-line reason, written to `type_probs.csv` next to the labels.
3. Disagreements that change the PET, and columns the model cannot place, are listed in `needs_review.csv` and printed as a warning by `detect` and `build`. Nothing is blocked.
4. The proving-ground scores do not get worse, and the 8-country silent misses drop sharply.
5. Real data never leaves the machine that runs the tool. The model runs offline on an ordinary laptop CPU.

## Non-goals (this round)

- **Number formats with checksums:** national IDs, phones, IBANs, plates, postcodes. They also have Finnish-only patterns today (`detect.py:34-62`), but the fix there is per-country validators (`python-stdnum`, a strict phone check), a separate, smaller task. Recorded as the next step.
- **Anything after detection:** role rules, table context, the selector, PETs, repair, red team, scorecard. The output feeds the same `privacy_role` and `subtype` labels the rest of the tool already reads.
- **Reading column headers.** Version 1 decides from values only, as the detector does today, so the README's claim "it never reads column names" stays true. A header as a weak hint is a later experiment.
- **Bigger word lists and a better-trained model.** After the hackathon.
- **Other tracks:** free-text redaction (track 4) and noisy counts (track 3).

## Anti-goals (a failure even if it works)

- Any real or proving-ground value sent to an outside service (Featherless, a cloud VM, any hosted model). Only fake and public data leaves the laptop.
- A model that sounds sure when it is not. An uncalibrated 0.9 is worse than no number.
- When the model decides alone, picking the single most likely type while a risky type is nearly as likely. "Category 0.55, surname 0.43" must not end as harmless.
- Breaking `main` or a teammate's work. Nothing lands on `main` without the evaluation passing.
- Model weights in git or in the submission zip (zip limit 100 MB).

## How the parts fit

```
column values ──► today's rules, unchanged (IDs, dates, numbers, keys, word lists, free text)
                    │                                     │
                    │ label L + which rule fired          │ every column that reaches the word-list stage
                    ▼                                     ▼
                 combine ◄──────────── semantic.py: model probabilities P per type + decision
                    │
                    ├─ L came from a word list ............ keep L
                    ├─ L is the fall-through "category" .... use the model's decision
                    ├─ L came from another rule ............ keep L
                    └─ any case: L and the model's top type get different PETs
                       and P(L's type) < 0.30 ............. warning + needs_review.csv (L stays)
                    ▼
            same privacy_role + subtype as today  +  type_probs.csv  +  needs_review.csv
```

- **Where it plugs in (author's call):** `classify` stays as it is, except that it also returns the name of the rule that fired. The model runs on every column that reaches the word-list stage (`detect.py:187`). Columns already labelled by an ID, card, phone, date, key, hostname or address pattern, and numeric columns, which leave for `_classify_numeric`, are not sent to it. The combine step follows the diagram.
  - **"Different PETs"** means the selector's candidate ladders for the two labels differ (`selector.candidates(role, subtype)`). So town against place name, which share a ladder, is not a disagreement. Name (drop only) against category (drop or keep) is one.
- **The switch:** `--semantic lexicon|hybrid`, so both can be scored on the same data. In the fork the default is `hybrid` when the model is installed. Without the optional libraries or the downloaded model it falls back to `lexicon` and says so.
- **The model:** a frozen, openly licensed multilingual sentence encoder (for example `intfloat/multilingual-e5-small`, MIT, about 470 MB, downloaded once like the spaCy models) turns each sampled value into a vector. The column vector is the mean and spread of those vectors plus about 20 shape statistics (length, capitals, digits, repeats). A small classifier (multinomial logistic regression or a two-layer network) maps that to the types. A calibration step (temperature scaling) then fixes the probabilities. Only the classifier and the calibration are ours; they are small enough to commit. Why not fine-tune a big model: it needs a GPU at run time, the weights cannot ship in the zip, and 17 hours is too short to do it well.
- **The decision rule, when the model decides alone.** Each type has a risk tier:
  - direct identifier: person name, street address;
  - quasi-identifier: town, place, organisation, occupation, language, sex;
  - free text;
  - harmless category.

  Default thresholds, tuned on the development set and then fixed:
  - top type at or above 0.80: **confident**, use it;
  - otherwise, the most protective type at or above 0.20: **protect anyway**, use that type, say so in the reason;
  - otherwise, or when the harmless class wins but the risky types together reach 0.20: **needs review**. The label is the most protective type at or above 0.20 (or the top type if none is), and the column gets a warning.
- **Warnings:** `needs_review.csv` has one row per flagged column: the label used, the model's top three types with probabilities, and the reason (disagreement or unclear). `detect` and `build` print the count and the column names; `build` copies the file into its results folder. Flags on the unseen HR export are listed the same way.
- **Dependencies (author's call):** the encoder libraries go in an optional extra (`pip install -e .[semantic]`), as the work split asks for new dependencies.

## Training data

All of it is fake or public; none of it is a real person.

| Source | What | Where it is made |
|---|---|---|
| Faker, every EU locale it supports (about 24) | names, streets, towns, companies, jobs, plus noise: case changes, blanks, extra spaces, prefixes | cloud VM or laptop (generation only) |
| Open-weight model on Featherless | lists of values Faker lacks or does badly, per language: occupations, sex and gender words, language names, clinic and department names, harmless categories (statuses, product types, triage words) | Featherless API; prompts ask for lists of words, never for people |
| Proving ground, 475 labelled columns | never training. Its six tuning datasets are the development set; the three held-out datasets are test | laptop |
| Scratch 8-country tables (seed 7, generator `gen_faker.py`) | development set; the generator moves into `scripts/` so the baseline can be rerun | laptop |
| Locked countries (author's call: Czech, Portuguese, Hungarian, fresh seed) | test only: generated once, never in training, not looked at until the final run | laptop |

**Splits (author's call):** rounds of fixes may look only at the development set (the 8-country tables and the six proving-ground tuning datasets). Published numbers come from the test set: the three held-out proving-ground datasets and the locked countries, each run once at the end. Anything that breaks this rule gets written down, as `results/detect/SPLIT.md` did for issue #23.

## Evaluation (what must pass before anything goes to `main`)

Committed as JSON in `results/detect-semantic/` (AGENTS.md: every published number from a committed JSON).

| Check | How | Must reach |
|---|---|---|
| E1 proving ground | `pets-eval detect`, hybrid against lexicon, held-out three (health, public_admin, customer_service) and all nine | role macro-F1 on no held-out dataset lower than lexicon (today 0.8202, 0.7241, 0.7821, `results/detect/*.json`). Subtype accuracy and the six tuning datasets are reported, not gated |
| E2 EU countries | development 8-country tables, then the locked countries once | counting only the model's types (name, street address, town, place, organisation, occupation, language, sex, free text): at most 1 of them labelled harmless per country. Number formats are reported separately |
| E2b unseen HR export | labels from both modes, compared column by column | every changed column listed with both labels and its warning. No score exists (the organisers hold the answers) |
| E3 calibration | expected calibration error (the average gap between stated and actual confidence) on the locked countries | reported with a reliability table; target at most 0.05 |
| E4 warnings | count of `needs_review` rows per dataset | reported; on the proving ground at most about 1 in 10 columns, so warnings stay worth reading |
| E5 cost | detect on all nine datasets on this laptop, CPU only | at most 3 times today's time; the one-time model download stated in the README |
| E6 tests | `pytest` | all existing tests pass; new tests for the combine step, the decision rule, the PET-ladder comparison, the warning output and the fallback to lexicon |

## Tools and where things run (author's call)

- **At run time:** nothing outside the laptop. The encoder is downloaded once from Hugging Face at a pinned revision; after that the tool runs offline.
- **Featherless ($25 credit):** generating value lists for training. Fake data only. The API key lives in an environment variable, never in a file in the repo.
- **Machine for embedding and training:** a teammate's Apple M5 MacBook (PyTorch `mps` backend) first; zray's laptop CPU second; a cloud GPU (Vultr, then Google Cloud) only if both are too slow. Reason (decided 2026-11-07): the job is about 900,000 short strings through a small encoder plus a logistic regression, minutes on a GPU and well under an hour on a laptop CPU, while the only Vultr GPU on offer was an 8x A100 machine at $12 an hour. The teammate's Mac generates the same fake corpus itself from the committed generator (same seed, pinned Faker version, hash checked), so no data file is copied between machines. Only fake data and our code go there.
- **Snowflake:** not used; it is a data warehouse and does not help here.

## Where the work happens

- **Fork:** `zraycd/team-1-trusted` (private, forked from `alex-1121/team-1-trusted`), branch `feat/semantic-types`. If the fork cannot be made (forking a private repo can be switched off), a branch in the team repo with the same name and the same rule: nothing merges to `main` until E1-E6 pass.
- **Telling the team:** this plan file is pushed to `main` (following the AGENTS.md git steps) so every teammate and their agents see it, with one line added to the README's status note.
- **Staying in sync:** the fork rebases on the team repo's `main` at every checkpoint below. `detect.py` changes on `main` are merged by hand, keeping what both sides meant.
- **Going back:** a pull request from the fork to the team repo, opened only when E1-E6 pass. If it is not open by Sunday 08:00, we present the word-list version and say in the video and README that the model is work in progress, with whatever numbers are committed.

## Schedule (Turku time)

| When | What |
|---|---|
| Sat 16:30 | Fork made, plan on `main`, accounts and keys set up (zray) |
| Sat 18:30 | Data generator and test sets ready; test sets frozen |
| Sat 20:30 | First model trained (teammate's M5 MacBook); E1 and E2 measured on the development set |
| Sun 00:00 | Calibration, decision rule, combine step, warnings, lexicon switch, tests |
| Sun 03:00 | Second round on development-set errors; final model; test-set run once; committed JSON |
| Sun 08:00 | Go or no-go: PR opened if E1-E6 pass, otherwise present the word-list version |
| Sun 10:00 | Submission closes (hard) |

## Limitations we will state

- Trained on fake data. Real exports are messier; the numbers say how it does on our test sets, not on any real hospital's data.
- A word-list match is trusted, so a wrong match is caught only when the model disagrees strongly enough to warn.
- Covers the types the word lists covered. National IDs, phones and postcodes outside Finland are the next step.
- Calibration is measured on countries we generated; a country or format we never generated can still fool it, which is what the warning is for.
- Warnings do not block a release. Someone must read them.

## Left to the builder

The exact encoder (open licence, multilingual, at most 500 MB, runs on CPU), the classifier type, the number of sampled values, the shape statistics, the prompt wording for Featherless, the locale list, and the threshold defaults within the rules above.

## Questions for the team

None open. The decisions above are zray's; the calls marked "author's call" are open to any teammate's note.
