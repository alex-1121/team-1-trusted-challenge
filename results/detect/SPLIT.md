# Detector held-out split

Written before the held-out run. Source: issue #15, `plans/2026-11-07-health-s1-spec.md` at commit `7d4a45c`.

## Tuning set (rules and thresholds were tuned while looking at these)

finance, cyber, education, mobility, energy, smart_city

The lexicons in `src/pets_transformer/lexicons/` are built from these six datasets only (`lexicons/build.py`, source columns named on the first line of each file).

## Held-out set (scored, never looked at while tuning)

health, public_admin, customer_service

Their data files and their `field_catalog.csv` rows were not opened while tuning. The catalog rows are read only after the final run, to report errors. No rule is changed after the held-out run, except the two listed below and the issue #23 rules.

## Rules added after the held-out run

Two rules were added after the first held-out run, in review, after inspecting the VALUES of the unseen HR export (`data/unseen/export_2025_q4.csv`). No labels exist for that file on our side, so no score drove them. They are generic Finnish formats, not fitted to any held-out dataset:

- HETU without its century sign (`DDMMYY` with a valid day and month, 3 digits, check character, checksum valid) is direct_identifier NATIONAL_ID. Seen in unseen column c05.
- An address with street, number, a comma, a 5-digit postcode and a place name in one field is direct_identifier STREET_ADDRESS, whatever its cardinality. Seen in unseen column c07.

Nothing else was changed on health, public_admin or customer_service. The held-out numbers before and after are both in `RESULTS.md`.

## Rules added in issue #23 (after the final #15 run)

These rules came from the review of the unseen export's VALUES and from public_admin's error list, both read after the final #15 run. The held-out catalog rows (health, public_admin, customer_service) were read to understand the errors. So the held-out scores after #23 are no longer a clean held-out measurement, most of all for public_admin. Every rule is a value-shape or table-structure rule; no column name or dataset is named in the code.

- Record key: unique values with one fixed letter prefix and a near-sequential trailing number (`SR-2024-000001`, at least half of the number range used) are the table's record key, before the first-unique-by-position fallback; other unique ids become technical_identifier. From public_admin's two record keys, which the hostname pattern took.
- Per-person number: a short-prefix number (`KC-4450`) that points at no other table's key, has 100 or more distinct values and repeats (distinct at most half the rows) is direct_identifier EMPLOYEE_ID. From unseen c02.
- Per-person hash: a hex hash column that maps one-to-one onto a direct or technical identifier of the same table is technical_identifier (a pseudonym), not non_sensitive. From unseen c20.
- Union pair: a code column with 2-30 values, blank on 5-95 % of rows, next to a two-decimal amount that is zero on exactly those rows (95 % agreement) makes both sensitive_attribute (code CATEGORY, amount FINANCIAL_DATA). From unseen c13 and c14.
- Monthly pay: two-decimal amounts whose 5th percentile is at least 1000, 95th at most 15000 and at most five times the 5th are sensitive_attribute FINANCIAL_DATA. From unseen c11.
- Occupation: a word also counts as an occupation when it ends with a Finnish title from `lexicons/occupation_words_fi.txt` (Finnish titles are compounds, lähi+hoitaja). From unseen c22; the lexicon words come from tuning data only.
- Phone: a value of exactly 8 digits starting with 0 and no separators is not a phone number. Review finding, no current column has this shape.
- HETU: a leading label word ("HETU 210390-945N") is dropped before the HETU check. From unseen c05, where 25 % of values carry the prefix.

## Scoring

```
cd <team-1-trusted>/data/proving-ground
pets-eval detect --pred <labels.csv> --datasets <dataset> --out <results/detect/<dataset>.json>
```

`--datasets` restricts the catalog to the one dataset, so columns of other datasets do not count as missing. Target: macro-F1 above 0.65 (organiser rule baseline B1, `docs/BENCHMARK.md`) on each held-out dataset.

## Inputs the detector reads

Column values only, at most 5000 rows per table, every CSV read with `dtype=str`. Column names are never read. Table structure is used: the first sequential prefixed id of a table is its record key (else the first unique id-shaped column), and a column whose values are another table's record keys is a foreign key.
