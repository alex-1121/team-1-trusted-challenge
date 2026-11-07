# Column-type model: development and test split

Written before the first evaluation run, 2026-11-07. Source: `plans/2026-11-07-eu-column-types.md` ("Splits"), Task 7 of `plans/2026-11-07-eu-column-types-implementation.md`.

## Development set (fixes may look at these)

- Proving ground, the six tuning datasets of `results/detect/SPLIT.md`: finance, cyber, education, mobility, energy, smart_city.
- The 8-country fake tables plus the mixed table: `data/semantic-eval/dev/` (fi_FI, de_DE, fr_FR, pl_PL, it_IT, es_ES, nl_NL, sv_SE, mixed_EU; hashes in `test_sets.json`).
- The calibration split of the training corpus: `calib.jsonl` (sk_SK, ro_RO, el_GR; hash in `corpus.json`). The head's temperature is fitted on it, so it is not a test set.
- The unseen HR export (`unseen`): no labels exist on our side; both modes' labels are compared (E2b). It is not scored.

## Test set (run once, at the end)

- Proving ground, the three held-out datasets: health, public_admin, customer_service. Note: `results/detect/SPLIT.md` already says their catalog rows were read during issue #23, so they are not a clean held-out set for the word-list rules. They are clean for the model: it was trained on fake data only and no threshold has been set while looking at them.
- The locked countries' tables: `data/semantic-eval/locked/` (cs_CZ, pt_PT, hu_HU). Generated and hashed (`test_sets.json`), never opened.
- The locked split of the training corpus: `locked.jsonl` (cs_CZ, pt_PT, hu_HU). `train.py` never reads it.

## Protocol

1. `evaluate.py --split dev` as often as needed. One round of fixes (until Sunday 03:00) may change only: the decision thresholds within the spec's rules, the corpus generator's noise and sources, and retrains through `scripts/semantic/TRAINING.md`. Each retrain gets a line under "Retrains" below.
2. `evaluate.py --split test` runs once. Its numbers are published as they come, misses written down as misses. The test split is not rerun.
3. Anything changed after the test run is listed under "Changed after the test run", with why.

The timing run (E5, `evaluate.py --cost`) runs detect on all nine proving-ground datasets in both modes and records only seconds, no labels and no scores, so it does not count as a look at the test set.

## Retrains

- 2026-11-07 19:44, first head: `dev-head1/train_report.json` (corpus hashes in `dev-head1/meta.json`, encoder revision 614241f622f53c4eeff9890bdc4f31cfecc418b3).
  Dev run (`dev-head1/`): EU tables gain a lot over lexicon, but mobility drops 0.8945 -> 0.7229 and cyber 0.8346 -> 0.7994. Cause: code-like category values (attack codes, lists of line numbers, course codes) read as STREET_ADDRESS; a false direct identifier in `stops` makes it a person table, so its places are no longer demoted to reference data.
- 2026-11-07 20:06, retrain 2 (corpus fix): about 35% of CATEGORY columns in the corpus are now written as codes (`code_value` in `gen_corpus.py`: letters and digits, dotted codes, snake_case, number lists, abbreviations, file names). Generic patterns, no value copied from the proving ground. Corpus hashes in `corpus.json`; head in `train_report.json` (calib accuracy 0.9561 -> 0.945, ECE 0.0154 -> 0.0245).
  Dev run (top-level `*_dev.json`): hybrid at or above lexicon on all six tuning datasets; warnings 32 -> 18 of 346 columns. EU macro-F1 lower than head 1 because head 1 labelled phone, plate and postcode columns STREET_ADDRESS by accident (right role, wrong reason); head 2's errors on those number-format columns are the same as lexicon's. Head 2 kept.

## Test run

Run once, 2026-11-07 20:35, on commit 68aa116 (head 2). Results in the `*_test.json` files. Against the spec's gates:

- E1 MISS. Role macro-F1, lexicon -> hybrid: health 0.8202 -> 0.7879, public_admin 0.7241 -> 0.7084, customer_service 0.7821 -> 0.7786. The gate was "no held-out dataset lower than lexicon"; all three are lower. Cause: six fall-through columns changed label, three for the worse and three wrong both ways. Code and category values (lab test codes and names, a permit project type) are read as place, organisation or town names, and the model was confident, so no warning was raised.
- E2 pass: no column of the model's types labelled harmless in cs_CZ, pt_PT or hu_HU. Macro-F1 lexicon -> hybrid: cs_CZ 0.5963 -> 0.7709, hu_HU 0.5053 -> 0.6806, pt_PT 0.5553 -> 0.6976.
- E3 pass: calibration error 0.0218 on `locked.jsonl` (1800 columns), 0.0412 on the locked tables (33 columns); target 0.05.
- E4 pass: 5 of 129 held-out columns flagged (3.9%).
- E5 pass (`e5_cost.json`): hybrid 2.71 times lexicon.

The test split is not rerun.

## Changed after the test run

None yet.
