# Column-type model: committed evidence

What each file here is. The model and its rules: `plans/2026-11-07-eu-column-types.md`. How the data is split and when the test split runs: `SPLIT.md`. Every JSON written by `scripts/semantic/evaluate.py` also records the commit, the encoder revision, the thresholds and the time. No file here holds a data value: only column names, labels, probabilities, counts and scores.

| File | What it holds | Written by |
|---|---|---|
| `SPLIT.md` | Which data is development and which is test, the run-once rule, and one line per retrain | by hand, before the first run |
| `test_sets.json` | SHA-256 hashes of the fake EU test tables (`data/semantic-eval/dev`, `.../locked`), the Faker version and the generator's hash | `scripts/semantic/gen_eu_tables.py` run, Task 5 |
| `corpus.json` | The training corpus command, Faker version, per-file SHA-256 and column counts, and the hashes of the generator and word lists, so anyone can rebuild the same corpus and check it | `scripts/semantic/gen_corpus.py` run |
| `train_report.json` | The committed head's training report: per-type F1, accuracy and calibration error (ECE) on the calibration countries (sk, ro, el), before and after temperature, the chosen temperature, the reliability table, encode speed | `scripts/semantic/train.py` |
| `e1_proving_ground_<split>.json` | Organisers' `score_detection` per proving-ground dataset, word lists only (`lexicon`) and word lists plus model (`hybrid`), and every column whose label changed | `evaluate.py --split` |
| `e2_eu_<split>.json` | Per fake EU country: macro-F1 both modes; columns of the model's types labelled harmless (gate: at most 1 per country); other columns (codes, numbers, dates) reported separately | `evaluate.py --split` |
| `e2b_unseen.json` | The unseen HR export: every column whose label differs between the two modes, with its warning flag. Not scored: the organisers hold the answers | `evaluate.py --split dev` |
| `e3_calibration_<split>.json` | ECE, accuracy and reliability table of the model on columns of its own types: corpus columns (`calib` or `locked`) and the EU test tables | `evaluate.py --split` |
| `e4_warnings_<split>.json` | Needs-review count and share per dataset and in total | `evaluate.py --split` |
| `e5_cost.json` | Seconds for detect on all nine proving-ground datasets in both modes on zray's laptop (CPU) | `evaluate.py --cost` |
| `advisor.json` | Advisor mode on every dataset: labels equal to word lists only (checked), each flag with its verdict (catch = the word-list role was wrong, false alarm = it was right), and the word-list errors not flagged. Made after the test run (`SPLIT.md`) | `evaluate.py --advisor` |
| `dev-head1/` | The development-split run of the first head, kept after retrain 2 replaced it, with that head's `meta.json` and `train_report.json`. Its JSONs show `uncommitted_changes: true` and an older commit because `evaluate.py` was not yet committed when it ran | `evaluate.py --split dev` |

Synthetic data: the EU tables and corpus are fake (Faker 40.44.0 and Featherless word lists). Proving-ground scores: TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0).
