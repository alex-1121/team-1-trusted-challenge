# Detector held-out split

Written before the held-out run. Source: issue #15, `plans/2026-11-07-health-s1-spec.md`.

## Tuning set (rules and thresholds were tuned while looking at these)

finance, cyber, education, mobility, energy, smart_city

The lexicons in `src/pets_transformer/lexicons/` are built from these six datasets only (`lexicons/build.py`, source columns named on the first line of each file).

## Held-out set (scored, never looked at while tuning)

health, public_admin, customer_service

Their data files and their `field_catalog.csv` rows were not opened while tuning. The catalog rows are read only after the final run, to report errors. No rule is changed after the held-out run, except the two listed below.

## Rules added after the held-out run

Two rules were added after the first held-out run, in review, after inspecting the VALUES of the unseen HR export (`data/unseen/export_2025_q4.csv`). No labels exist for that file on our side, so no score drove them. They are generic Finnish formats, not fitted to any held-out dataset:

- HETU without its century sign (`DDMMYY` with a valid day and month, 3 digits, check character, checksum valid) is direct_identifier NATIONAL_ID. Seen in unseen column c05.
- An address with street, number, a comma, a 5-digit postcode and a place name in one field is direct_identifier STREET_ADDRESS, whatever its cardinality. Seen in unseen column c07.

Nothing else was changed on health, public_admin or customer_service. The held-out numbers before and after are both in `RESULTS.md`.

## Scoring

```
cd <team-1-trusted>/data/proving-ground
pets-eval detect --pred <labels.csv> --datasets <dataset> --out <results/detect/<dataset>.json>
```

`--datasets` restricts the catalog to the one dataset, so columns of other datasets do not count as missing. Target: macro-F1 above 0.65 (organiser rule baseline B1, `docs/BENCHMARK.md`) on each held-out dataset.

## Inputs the detector reads

Column values only, at most 5000 rows per table, every CSV read with `dtype=str`. Column names are never read. Table structure is used: the first unique id-shaped column of a table is its record key, and a column whose values are another table's record keys is a foreign key.
