# pets-eval: install and use

`pets-eval` is the organisers' self-assessment toolkit. It is a small Python package (MIT, Since AI ry) inside the proving ground at `data/proving-ground/toolkit/`. It scores our work the way the final demo needs: what risk we removed and what utility we kept. Its score is a self-assessment, not the official judging score (`proving-ground/docs/EVALUATION.md`).

## Install (once per machine)

Needs Python 3.10 or newer and the data restored (`../data/README.md`). Tested 2026-11-06 with Python 3.13 and uv; plain `python3 -m venv` works too.

```bash
cd team-1-trusted
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -e data/proving-ground/toolkit
source .venv/bin/activate
```

Run every command from `data/proving-ground/`, because the CLI looks for `metadata/` relative to the current folder.

```bash
cd data/proving-ground
pets-eval scenarios                      # the 27 sharing scenarios (id, access type, title)
pets-eval tasks --dataset health         # utility tasks of one dataset, with what each needs
pets-eval check my_out/                  # scan an output for leftover identifiers
```

## The six commands and when we use them

| Command | What it does | Demo item it feeds |
|---|---|---|
| `scenarios` | Lists the sharing scenarios | 5: pick one, design for it |
| `tasks --dataset X` | Lists the utility tasks and what each needs (a join, a pseudonym, a column) | 4: know what we must keep |
| `detect --pred labels.csv` | Scores our field classification (`dataset,table,column,privacy_role,subtype`) against `metadata/field_catalog.csv` | 1: data types identified |
| `text --gold spans.jsonl --pred spans.jsonl` or `--protected redacted.csv` | Scores free-text redaction: span precision, recall, F2, or which gold values survive | 1 and 3 for text |
| `check folder/` | Scans output for HETU, IBAN, card, email, phone, IP, MAC, plate patterns | 3: nothing leaked |
| `scorecard --original data/X --protected out/X --scenario ID` | Privacy risk components, utility per task, composite; JSON and HTML | 4 and 5: before vs after, residual risk |

## Output folder rules for `scorecard`

- Same file names as the original tables; a table we do not ship is reported as withheld.
- Keep original column names for kept columns. Generalised values are understood: `30-39`, `90+`, `201**`, `2025-03`, `2025-W12`, rounded coordinates, 3-character ICD-10 codes.
- Each released row-level table needs `rowmap_<table>.csv` (`protected_row`, `original_record_id`) next to it, for scoring only. Never commit it, never zip it.
- A table with no row map and no original ids is scored as synthetic data (distance to closest record, membership inference against `holdout/`).
- For the health DP workload, add `dp_answers.csv` (`id,value`) and state epsilon, delta, the unit of privacy and the contribution bound.

Privacy score = 1 - (0.5 x worst risk + 0.5 x mean risk). Composite = weighted harmonic mean of privacy (30) and utility (25). Releasing nothing and releasing everything both score low.

## Python API

`pets_eval.privacy` (k-anonymity, l-diversity, t-closeness, uniqueness, small cells, differencing, DCR/NNDR, membership inference, trajectory unicity), `pets_eval.attacks` (linkage, attribute inference, hash dictionary attack, HETU enumeration), `pets_eval.text`, `pets_eval.detect`, `pets_eval.parse`, `pets_eval.utility`. Baseline scripts in `data/proving-ground/baselines/` show the API in use; `examples/quickstart.py` protects `health/ed_visits` for HEALTH-S1 and writes a scorecard (about a minute).

Source: `proving-ground/toolkit/README.md`, `proving-ground/docs/EVALUATION.md`, `proving-ground/START_HERE.md`; the install was run on 2026-11-06.
