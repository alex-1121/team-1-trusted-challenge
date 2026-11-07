# Detector held-out split

Written before the held-out run. Source: issue #15, `plans/2026-11-07-health-s1-spec.md`.

## Tuning set (rules and thresholds were tuned while looking at these)

finance, cyber, education, mobility, energy, smart_city

The lexicons in `src/pets_transformer/lexicons/` are built from these six datasets only (`lexicons/build.py`, source columns named on the first line of each file).

## Held-out set (scored, never looked at while tuning)

health, public_admin, customer_service

Their data files and their `field_catalog.csv` rows were not opened while tuning. The catalog rows are read only after the final run, to report errors. No rule is changed after the held-out run.

## Scoring

```
cd <team-1-trusted>/data/proving-ground
pets-eval detect --pred <labels.csv> --datasets <dataset> --out <results/detect/<dataset>.json>
```

`--datasets` restricts the catalog to the one dataset, so columns of other datasets do not count as missing. Target: macro-F1 above 0.65 (organiser rule baseline B1, `docs/BENCHMARK.md`) on each held-out dataset.

## Inputs the detector reads

Column values only, at most 5000 rows per table, every CSV read with `dtype=str`. Column names are never read. Table structure is used: the first unique id-shaped column of a table is its record key, and a column whose values are another table's record keys is a foreign key.
