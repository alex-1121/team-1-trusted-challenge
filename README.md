# TrustED PETs Transformer

Since AI Hackathon 2026, Turku, 6-8 November. TrustED challenge: protect the data, keep its value.

## What this tool does

It takes a dataset and a sharing scenario (who gets the data, and why). In one command it:

1. **Detects** what every column holds (a name, a birth date, a diagnosis code, ...). It reads the values only, never the column names, so it also works when headers are hidden (the `unseen` dataset names its columns `c01` to `c26`).
2. **Chooses** a privacy-enhancing transformation (PET) for each column, such as dropping it, turning a birth date into a 10-year age band, or replacing an ID with a keyed token.
3. **Transforms** the data, then fixes the rows that are still easy to single out.
4. **Measures** the result with the organisers' own scorecard (`pets-eval`) and with extra attacks of our own.
5. **Releases** the protected tables only if every check passes. If a check fails, it writes nothing and tells you why.

All data here is the synthetic TrustED PETs Proving Ground. No real person's data is used.

---

## Quick start (about 10 minutes)

### What you need

- Linux or macOS (on Windows, use WSL).
- Python 3.10 or newer (`python3 --version`).
- `ssh-keygen`, which comes with OpenSSH and is already on most machines (`which ssh-keygen`). The tool uses it to check the signature on each scenario's rules.
- The proving-ground zip from the organisers: `TRUSTED_PETS_PROVING_GROUND_2026 (1).zip`.
- About 2 GB of free disk space.

### Step 1: Get the code

```bash
git clone https://github.com/alex-1121/team-1-trusted.git
cd team-1-trusted
```

Run every command in this README from this folder (the repo root).

### Step 2: Put the data in place

The data is not in the repo. Unzip the proving-ground zip into `data/` and rename the folder it makes to `proving-ground`:

```bash
unzip "/path/to/TRUSTED_PETS_PROVING_GROUND_2026 (1).zip" -d data/
mv data/TRUSTED_PETS_PROVING_GROUND_2026 data/proving-ground
ls data/proving-ground/START_HERE.md      # must print the file name
```

If you have the bigger organiser bundle `TRUSTED_SinceAI2026_FINAL.zip`, the proving-ground zip is inside it: unzip the bundle first. Only the end result matters: the folder holding `START_HERE.md`, `data/`, `metadata/` and `toolkit/` must be at `data/proving-ground/`.

### Step 3: Install

The virtual environment must be called `.venv` and sit in the repo root, because the tool looks for the organisers' `pets-eval` at `.venv/bin/pets-eval`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e data/proving-ground/toolkit    # the organisers' pets-eval
pip install -e .                              # our tool
```

In a new terminal later, run `source .venv/bin/activate` again before the commands below.

### Step 4: Check that it works

```bash
pip install pytest
pytest -q
```

You should see `267 passed, 1 skipped` within a few seconds.

You are set up.

---

## Make a protected copy of the data for a scenario

One command per scenario. Each writes into its own folder, `out/<SCENARIO>/`, so runs never mix and the evidence committed in the repo is not overwritten.

**HEALTH-S1**, our main scenario: a hospital shares its emergency-department visits and lab results with a university research group. About 2.5 minutes.

```bash
python -m pets_transformer.cli build --scenario HEALTH-S1 \
    --submission out/HEALTH-S1/release --results out/HEALTH-S1/report
```

When it is done it prints:

```
built HEALTH-S1: 58 plan rows, results in out/HEALTH-S1/report
```

A warning that the "semantic model" is unavailable is normal. That model is optional (see "Optional extras" below).

### All scenarios

These are the scenarios the tool can build. Each needs rules signed by a data steward in `policy/`, and these five have them. Copy a command as it is.

| Scenario | Who gets the data | Time |
|---|---|---|
| HEALTH-S1 | University research group, in a controlled research environment | ~2.5 min |
| HEALTH-S3 | AI vendor training a triage-support model | ~20 s |
| EDU-S2 | Ed-tech vendor training a drop-out early-warning model | ~15 s |
| ENERGY-S3 | Energy-poverty researchers (1.6 million hourly meter readings) | ~2 min, needs a few GB of memory |
| PUB-S3 | Research group studying service equity | ~2 min, **refused on purpose** (see below) |

```bash
python -m pets_transformer.cli build --scenario HEALTH-S1 \
    --submission out/HEALTH-S1/release --results out/HEALTH-S1/report

python -m pets_transformer.cli build --scenario HEALTH-S3 --contract contracts/generated/HEALTH-S3.auto.json \
    --submission out/HEALTH-S3/release --results out/HEALTH-S3/report

python -m pets_transformer.cli build --scenario EDU-S2 --contract contracts/generated/EDU-S2.auto.json \
    --submission out/EDU-S2/release --results out/EDU-S2/report

python -m pets_transformer.cli build --scenario ENERGY-S3 --contract contracts/generated/ENERGY-S3.auto.json \
    --submission out/ENERGY-S3/release --results out/ENERGY-S3/report

python -m pets_transformer.cli build --scenario PUB-S3 \
    --submission out/PUB-S3/release --results out/PUB-S3/report
```

`--contract` points at the column-by-column plan our selector wrote for that scenario, which the data steward signed. HEALTH-S1 and PUB-S3 keep theirs in `contracts/` and find it on their own.

PUB-S3 shows the tool saying no. Its research tasks (area counts and a 1 km hotspot map) cannot both survive the privacy protection in one row-level table, so the build stops with `red-team gate FAILED (...)` and releases nothing. That is the expected result. The report folder still explains why.

### What you get

```
out/HEALTH-S1/
├── release/                      the protected data
│   ├── health/
│   │   ├── ed_visits.csv         protected table
│   │   ├── lab_results.csv       protected table
│   │   ├── rowmap_ed_visits.csv  for scoring only, never for the recipient
│   │   └── rowmap_lab_results.csv
│   ├── health_field_labels.csv   what we detected in each column
│   ├── unseen_field_labels.csv   our labels for the organisers' unlabelled HR export
│   └── release_record.json       hashes of the released files, recipient, purpose, residual risks
└── report/                       how and why
    ├── summary.md                start here: before and after, per task and per risk
    ├── plan.md                   one row per column: detected type, PET chosen, reason
    ├── scorecard.html / .json    the organisers' scorecard of this release
    ├── redteam.json              our extra attacks and the pass/fail gate
    └── checks/                   l-diversity, informed attacker, joined-table k
```

Open `out/HEALTH-S1/report/summary.md` first; `plan.md` explains every choice column by column.

The row maps (`rowmap_*.csv`) link each protected row back to its original row. The scorecard needs them, but they are never published or given to a data recipient (organiser rule).

### How to run a new scenario

Any of the 27 organiser scenarios in `data/proving-ground/metadata/scenarios.json` can be built, and each already has its "before" scorecard in `baseline-scores/`. Pick one that has no file in `policy/` yet, for example CITY-S1 (a city publishes footfall counts as open data). Everything goes to `out/<scenario>/` except the policy, which the build reads only from `policy/`. From the repo root, with `.venv` active:

1. **Choose the scenario.**

   ```bash
   ID=CITY-S1
   ```

2. **Let the selector write the contract**, the column-by-column plan (a few minutes):

   ```bash
   python -m pets_transformer.cli select --scenario $ID \
       --out out/$ID/contract.json --evidence out/$ID/selection.json
   ```

   It prints one line per column. Look at the first line, `reference (...)`: the required tasks scored with every column at its finest option. A task at `0.0000` there cannot be served by any choice the selector makes, and the build will refuse.

3. **Draft the policy**, the limits the release must meet:

   ```bash
   python -m pets_transformer.cli draft-policy --scenario $ID --contract out/$ID/contract.json
   ```

   This writes `policy/$ID.policy.json`: recipient, purpose and required tasks from the scenario, the same attack limits as our signed policies, k and l from the contract, and the contract's sha256, so the build accepts this contract and no other. It never overwrites an existing policy. Open the file and check it; that is the data steward's part.

4. **Build** (about the same time again):

   ```bash
   python -m pets_transformer.cli build --scenario $ID --contract out/$ID/contract.json \
       --skip-signature --submission out/$ID/release --results out/$ID/report
   ```

   `--skip-signature` is for demo runs only. It reads the policy without checking the steward's signature. Every limit and the contract hash still apply, and `release_record.json` says `"skipped"` for the signature. A real release has the steward sign the policy ("Signing a policy" in `docs/technical-details.md`) and runs without the flag.

5. **Read the result**: `out/$ID/report/summary.md` first, then `out/$ID/report/redteam.json` for the gate's verdict and reasons. On a pass, the protected tables are in `out/$ID/release/`. A refusal is a result too: it says which limit or task the release missed.

   A pass means every check the gate runs passed, not that the release is safe. Read the privacy risk table in `summary.md` too: the gate does not read every number in it (see CITY-S1 below).

We first ran this on FIN-S2 (a bank shares card transactions with an AI vendor), with the hand-written policy `policy/FIN-S2.policy.json`. The pipeline runs end to end on finance (selector 3.3 min, build 1.5 min on a laptop), and the gate **refuses** the release, for three reasons (`results/fin-s2-build/builds.jsonl`):

- FIN-U4 and FIN-U6 are not measured. Both need `card_pan` as a stable pseudonym (a consistent stand-in for the card number). Our detector labels it a direct identifier, whose only option is drop. With those two tasks at 0 from the start, the selector also withheld the `cards` and `customers` tables that FIN-U6 needs.
- The organisers' scorer finds groups smaller than 5 on `amount_eur` and `currency` (smallest group 1). Our repair enforced k of 5 on `amount_eur` alone.

The one task that could run, FIN-U1 (the fraud model), keeps 0.7966 of its original score, and privacy is 0.999 (`results/fin-s2-build/scorecard.json`). Nothing was released. Fixing it needs a pseudonym option for direct identifiers that a required task uses as a key.

We then followed the five steps above word for word on CITY-S1 (selector 1 min, build 1 min). The gate **passes**, and that pass is wrong for open data. The selector withheld the footfall counts and released the raw WiFi probes instead: one row per probe, with the sensor, the date and hour, and a keyed token for each phone's MAC address. The organisers' scorecard rates privacy 0.412 (0.225 before) because 0.882 of the phones can be singled out by their trail of sensors and hours ("trajectory unicity", `results/city-s1-build/scorecard.json`). Our fingerprint attack only counts facts that stay the same for a person, so it reports "not applicable" here, and the gate never reads the scorecard's trajectory number (`results/city-s1-build/redteam.json`). The selector also ignores that the recipient is "anyone": it decides on the required tasks alone. Do not use this CITY-S1 release.

---

## Run your own evaluation on our output

The protected tables are plain CSV files in the layout `pets-eval` expects: the same file names, the original names for kept columns, and a row map next to each table. Point any evaluation script at `out/<SCENARIO>/release/<dataset>/`.

With the organisers' `pets-eval`, from the repo root, with `.venv` active:

```bash
# Privacy and utility scorecard (about 15 s)
pets-eval scorecard --root data/proving-ground \
    --original data/proving-ground/data/health \
    --protected out/HEALTH-S1/release/health \
    --scenario HEALTH-S1 --out out/HEALTH-S1/judge-scorecard

# Scan the release for leftover identifiers (HETU, IBAN, email, phone, ...)
pets-eval check out/HEALTH-S1/release/health

# Score our column detection against the organisers' field catalogue
pets-eval detect --root data/proving-ground --datasets health \
    --pred out/HEALTH-S1/release/health_field_labels.csv
```

Good to know:

- Always give `pets-eval scorecard` an `--out` folder. Without it the scorecard is written into the release folder, and a later build into that folder refuses to run, because it finds files it did not write.
- `--root data/proving-ground` lets `pets-eval` run from the repo root. Without it, `cd data/proving-ground` first.
- For another scenario, change the scenario id and the dataset folder: HEALTH-S3 uses `health`, EDU-S2 `education`, ENERGY-S3 `energy`.

When we ran exactly these three commands after a fresh HEALTH-S1 build, the scorecard gave privacy 1.0, utility 0.971, composite 0.9866; the identifier scan found no residual direct identifiers; and detection on health scored macro-F1 0.8202. These match our committed `results/health-s1-build/scorecard.json` and `results/detect/health.json`. Every build draws a new secret key and a new row order, so your scores can differ slightly.

### Detect only, on any dataset

To label the columns of a dataset without protecting it (about 10 s):

```bash
python -m pets_transformer.detect --data data/proving-ground/data/education \
    --dataset education --out out/labels/education.csv

pets-eval detect --root data/proving-ground --datasets education --pred out/labels/education.csv
```

The labels use the `pets-eval detect --pred` format: `dataset,table,column,privacy_role,subtype`.

---

## If a build stops

The build checks its own output and refuses to release anything that fails. It prints `red-team gate FAILED (<reasons>)` and names the `redteam.json` file with the details.

| What you see | What it means | What to do |
|---|---|---|
| `red-team gate FAILED` on HEALTH-S1, HEALTH-S3, EDU-S2 or ENERGY-S3 | Each build uses a new random row order and key; rarely, one draw fails an attack | Read the reasons, then run the same command once more |
| `red-team gate FAILED` on PUB-S3 | Expected: the utility check refuses this scenario | Nothing; this is the demo of a refusal |
| `build needs data/proving-ground/...` | The data is not where the tool expects it | Redo Step 2 |
| `pets-eval` not found, or a scorecard error | `pets-eval` is not installed in `.venv` at the repo root | Redo Step 3 |
| A refusal that names a file in the submission folder | The release folder holds a file this build did not write | Use a fresh `--submission` folder, or move that file away |
| A refusal about the policy, its signature or the contract hash | Only the five scenarios above have signed rules, and only with the contract shown | Use one of the five commands exactly as written; for a new scenario see "How to run a new scenario" |

---

## Optional extras

**Multilingual column-type model.** Off unless installed. It flags columns the word lists may have missed (for example a German surname column) for a person to review. By default it changes no label.

```bash
pip install -e ".[semantic]"
python -m pets_transformer.semantic.model --download    # 471 MB, the only network call
```

Once installed, `build` and `detect` take `--semantic advisor` (the default then: flags only), `--semantic hybrid` (the model also labels the columns the word lists cannot place) or `--semantic lexicon` (word lists only).

**Everything else**: the separate commands (`select`, `protect`, `score`, `checks`, `redteam`), every option, and how a data steward signs a scenario's rules are in `docs/technical-details.md`.

---

## Our results at a glance

Scores from the organisers' `pets-eval` scorecard, 0 to 1, higher is better. They are our own self-assessment, separate from the official judging score. "Before" is the original data released with no protection.

| Scenario | Privacy before → after | Utility before → after | Composite before → after | Released? |
|---|---|---|---|---|
| HEALTH-S1 | 0.1716 → 1.0 | 1.0 → 0.971 | 0.2752 → 0.9866 | yes |
| HEALTH-S3 | 0.1728 → 1.0 | 1.0 → 1.0 | 0.2769 → 1.0 | yes |
| EDU-S2 | 0.219 → 1.0 | 1.0 → 0.9963 | 0.3395 → 0.9983 | yes |
| ENERGY-S3 | 0.2275 → 1.0 | 1.0 → 1.0 | 0.3506 → 1.0 | yes |
| PUB-S3 | 0.0833 → 1.0 | 1.0 → 0.5547 | 0.1429 → 0.7327 | no, refused by the utility check |

Sources: "before" from `baseline-scores/<dataset>_<SCENARIO>_<recipient>_raw.json`, "after" from `results/<scenario>-build/scorecard.json` (for example `results/health-s1-build/scorecard.json`). Composite is the organisers' weighted harmonic mean of privacy (weight 30) and utility (weight 25).

On HEALTH-S1, our own red team broke an earlier release that the scorecard had rated 0.9709 (`results/redteam/before-7cf541b.json`). The current release passes all five of our extra attacks (`results/health-s1-build/redteam.json`). What an attacker can still do, in plain words: `docs/guarantee-and-residual-risk.md` and `LIMITATIONS.md`.

The full write-up, with every number and the file it comes from: `docs/technical-details.md`.

---

## What is in this repo

One row per top-level file and folder. Files inside `context/` and `team/` are listed one by one in `context/README.md`.

| Path | What it holds |
|---|---|
| `context/` | The official brief, one-pager, video transcript, source file list, challenge digest, and the organiser docs in `context/proving-ground/`. `context/README.md` indexes every file here and in `team/` |
| `team/` | The submission checklist |
| `data/` | The proving-ground data, gitignored; `data/README.md` says how to restore it |
| `contracts/` | One JSON contract per scenario: recipient, purpose, role rules (by detected role), named column rules with their reasons, and the k target with its repair ladder. `HEALTH-S1.json` is the selector v2 output; `HEALTH-S1.handwritten.json` the hand-written start; `HEALTH-S1-noflag.json`, `HEALTH-S1-pseudonym.json` and `HEALTH-S1-informed.json` are variants for team decisions (`docs/technical-details.md`); `PUB-S3.json` is the selector's PUB-S3 contract after a reviewer's edit; `generated/` holds the contracts the selector wrote for HEALTH-S3, EDU-S2, ENERGY-S3, PUB-S3 and FIN-S2 |
| `policy/` | One JSON policy per scenario we build, with the limits the release must meet, the recipient, the purpose and the contract hashes the data steward allows. `build` runs only when the policy's signature verifies against `policy/allowed_signers` (see "Signing a policy" in `docs/technical-details.md`), or with `--skip-signature` for demo runs. `draft-policy` writes an unsigned one for a new scenario; `FIN-S2.policy.json` is unsigned, for the first FIN-S2 run |
| `src/pets_transformer/` | The code: `detect` (labels), `selector` (writes the contract), `pets` and `protect` (the transformations), `repair` (k and l on the rows at risk), `generalise` (what a coarsened value can stand for), `score` (the organisers' scorecard), `checks` and `redteam` (attacks the scorecard does not run), `policy` (the signed limits and the release record), `build` (one command for all of it), `contract`, `sweep` and the command line `cli`; `semantic/` is the optional column-type model (type list, decision rule, features, offline loader and the committed head in `semantic/models/`); by default it only flags columns for review (advisor mode) |
| `tests/` | pytest suite for detect (word lists and the hybrid type model), protect, score, checks, the repair sweep, the release gate (tokens, shuffle, repair, hour ranges, selector, new PETs, attacks), what the gate refuses (`test_gate.py`) and the command-line wiring |
| `scripts/` | `scripts/semantic/` makes the fake EU test tables and training corpus, the Featherless word lists (`llm_values/`), trains the type model (`train.py`, runbook `TRAINING.md`) and evaluates it |
| `results/` | Committed evidence: detector results (`detect/`), the column-type model's evidence (`detect-semantic/`, indexed in its `README.md`), the selector's evidence (`selection/`), the red-team gate on the earlier release (`redteam/`), the repair sweep (`sweep/`), the repository audit of 2026-11-07 (`audit-2026-11-07/`), and one `<scenario>-build/` folder per build (scorecard, repair search, checks, red team), including the HEALTH-S1 variants |
| `baseline-scores/` | "Before" scorecards: every original table scored unprotected, one HTML + JSON pair per scenario, named `<dataset>_<SCENARIO>_<recipient>_raw` |
| `pets_submission/` | What goes to the organisers on request; only the two label files are committed |
| `demo/` | `the-er-register.html`: the demo-video sequence. A printed sheet of patient records is redacted in blue halftone, shuffled, stamped, folded, addressed and sent; it ends on the HEALTH-S1 numbers. One self-contained HTML file, no build step |
| `docs/` | `technical-details.md` (the full write-up: method, every number with its source, every command option, policy signing), pitch deck outline, demo video script, what HEALTH-S1 guarantees and its residual risk, and the `pets_submission/` handover |
| `attack_analysis.md` | What `pets-eval` actually measures: risk checks, utility tasks, how the score is aggregated, blind spots |
| `LIMITATIONS.md` | What our tool does not do yet: separate releases can be linked, flagged columns do not stop the release, word lists and model come from synthetic data |
| `decisions.md` | Team decision log |
| `AGENTS.md` | Rules for every teammate's coding agent |
| `CLAUDE.md` | One line that imports `AGENTS.md` for Claude Code; holds no rules |
| `README.md` | This file: set up, run, evaluate |
| `pyproject.toml` | Package definition for `pets_transformer`; optional extras `semantic` (the type model at run time) and `train` (corpus and training) |
| `.gitignore` | Keeps the proving-ground data, the attack answer keys (row maps, truth, holdout), protected tables, bulky outputs (including `out/`), the fake corpus and EU test tables (`data/semantic-*`) and secrets out of git |

## Rules we hold ourselves to

The rules live in `AGENTS.md` (data, claims, writing). Short version: synthetic or allowed data only, no privacy claim without method and parameters, every number from a committed scorecard, nothing from truth/, holdout/ or rowmap_*.csv in git or the zip.

## Attribution

TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0). The challenge is inspired by the European project TrustED (Horizon Europe grant agreement No. 101168467); this repository is not a TrustED deliverable.
