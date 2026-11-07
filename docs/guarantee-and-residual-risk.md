# HEALTH-S1: what we guarantee, what we do not, and which attacks we ran

Scenario HEALTH-S1: a hospital gives its emergency-department (ED) visits and lab results to a university research group in a research environment (a known recipient, no public release) (`contracts/HEALTH-S1.json`). Every number below is followed by the file it comes from. Scorecard numbers are our self-assessment from the organisers' `pets-eval`, not the official judging score.

## What we guarantee

Each line is a method with its parameters, applied by `protect` from `contracts/HEALTH-S1.json`. The per-column table is `results/health-s1-build/plan.md`.

- **Keyed pseudonym for the patient.** `patient_hetu` (the Finnish national id) is replaced by "P" plus the first 16 hex characters of HMAC-SHA256 over the original value. The key is 32 random bytes, written to `out/health-s1-build/hmac.key` when the output folder is first built, outside the released folder and never committed. The same key serves every table in a run, so a patient keeps one pseudonym and revisits still link. Without the key, a dictionary attack (hashing every possible id and comparing) cannot reverse it.
- **k measured, and stated.** k is the size of the smallest group of rows sharing the same quasi-identifier values (a quasi-identifier identifies someone only in combination with others). The scorer measures k on ed_visits over the catalogued quasi-identifiers: date_of_birth (now a 10-year age band), sex, municipality (eight largest exact, the rest "other"), arrival hour and arrival_mode. Result: k<5 share 0.1817, k<2 share 0.0384, median k 15, min k 1, 6810 groups over 46398 rows (`results/health-s1-build/scorecard.json`). Our own k, over age band, sex, municipality and arrival hour without arrival_mode, gives a k<5 share of 0.0779 (`results/health-s1-build/summary.md`).
- **Hour of day only.** `arrival_ts` keeps only "HH:00". The date is gone (`results/health-s1-build/plan.md`).
- **Listed columns dropped.** From ed_visits: patient_name, phone, home_address, postcode, ambulance_unit, chief_complaint, attending_physician_id, attending_physician_name, discharge_ts (`results/health-s1-build/scorecard.json`). date_of_birth is overwritten by the age band. From lab_results: sampled_ts (`results/health-s1-build/plan.md`).
- **Two tables withheld.** clinical_notes (free text with identifying detail, no task uses it, no redactor in scope) and published_weekly_stats (a second linkage path by week, municipality and age band, no task uses it) are not written at all (`contracts/HEALTH-S1.json`).
- **No direct identifier pattern left.** The organisers' regex scan found no residual direct identifiers in the 6 files of the output (`results/health-s1-build/check.txt`). The scan is pattern-based: it finds identifier formats, not every identifying fact.

## What we do not guarantee

- **Not every row has k of at least 5.** The scenario's target is k of at least 5 on the named columns (`plans/2026-11-07-health-s1-spec.md`, user story 4). On the scorer's column set the k<5 share is 0.1817 (`results/health-s1-build/summary.md`), so 18.2% of ed_visits rows sit in groups of fewer than 5. The target is not met for all rows.
- **Why we did not push k further.** In the sweep, 20-year age bands drop the revisit task H-U6 to 0.0271, and 2- or 3-hour arrival blocks drop the arrival curve H-U8 to 0.0 (`results/sweep/sweep.md`). The chosen cell, 10-year bands and 1-hour blocks, has the best composite, 0.9346 (`results/sweep/sweep.md`). We traded the k<5 share for the research tasks and say so.
- **Shipped attackers only.** The scorer ran the attacker files that ship with the toolkit. A stronger attacker with more background knowledge or other outside data was not tested (`results/health-s1-build/summary.md`).
- **No dates, so no seasonality.** A researcher cannot study weekly or seasonal patterns on this release (`contracts/HEALTH-S1.json`).
- **The linkage result may be optimistic.** Linkage re-identification fell from 0.5697 to 0.0 (`results/health-s1-build/summary.md`). The linkage attacker reads date_of_birth as a date, and a band such as "30-39" does not parse as one, so that attacker may get no age information from it. We have not tested this (`results/health-s1-gate/GATE.md`).
- **Clinical values are kept as they are.** Diagnosis codes, vital signs and lab values are released unchanged because the study needs them (`results/health-s1-build/plan.md`). Someone who already knows a patient's exact readings could use them. No attack for that was run.
- **The key is per output folder.** A rerun into the same `out/` folder reuses the key, so pseudonyms stay the same across those runs. A new key needs a new output folder.

## Attacks run

From `results/health-s1-build/summary.md`, before and after:

| Attack or check | Before | After |
|---|---|---|
| ed_visits: direct identifiers retained | 1.0 | 0.0 |
| ed_visits: records with k<5 | 1.0 | 0.1817 |
| ed_visits: linkage re-identification (shipped attacker files) | 0.5697 | 0.0 |
| ed_visits: free-text identifier leakage | 0.0 | 0.0 |
| lab_results: direct identifiers retained | 0.0 | 0.0 |

Two more checks ran. The dictionary attack on hashed columns is listed as run in `results/health-s1-build/summary.md`; the scorecard JSON gives it no separate number. The direct-identifier pattern scan (`pets-eval check`) ran on the protected output only and found no residual hits (`results/health-s1-build/check.txt`).

Scores: privacy 0.1716 before (`baseline-scores/health_HEALTH-S1_research-env_raw.json`) and 0.891 after; utility 1.0 before and 0.9928 after; composite 0.2752 before and 0.9346 after (`results/health-s1-build/scorecard.json`).

TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0)
