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

Scores before: privacy 0.1716, utility 1.0, composite 0.2752 (`baseline-scores/health_HEALTH-S1_research-env_raw.json`). After: privacy 0.891, utility 0.9928, composite 0.9346 (`results/health-s1-build/scorecard.json`).

## Checks the scorecard does not run

The organisers' scorecard does not run these three checks, so we wrote them ourselves: `python -m pets_transformer.cli checks`, code in `src/pets_transformer/checks.py`. Each JSON names the command, the columns and the thresholds it used. They hold counts and rates only: no diagnosis, no row-map entry and no value of any group. The first run was on the merged release (`results/checks/`). That run led to one change, dropping arrival_mode (see the first check). The second run is on the release after that change (`results/checks-l/`).

- **Mixed diagnoses (l-diversity).** l-diversity asks whether the rows in a group share one diagnosis or a mix. A group is the set of rows with the same age band, sex, municipality, arrival hour and arrival_mode. We count the distinct icd10_primary codes in each group. On the merged release, 0.2787 of the 6810 groups have fewer than 2 distinct diagnoses and 0.4439 have fewer than 3. Those groups hold 0.0438 and 0.0966 of the rows. The worst group has 4 rows and 1 diagnosis (`results/checks/l_diversity.json`). Fix applied: arrival_mode is dropped from ed_visits by a named rule in `contracts/HEALTH-S1.json`. No HEALTH-S1 task reads it, and wider age bands or hour blocks break H-U6 and H-U8 (`results/sweep/sweep.md`). After the fix, 0.1128 of the 3811 groups have fewer than 2 distinct diagnoses and 0.2359 have fewer than 3. Those groups hold 0.0100 and 0.0320 of the rows. The worst group is still 4 rows with 1 diagnosis (`results/checks-l/l_diversity.json`). The finding stands: in about 1 group in 9, knowing a patient's age band, sex, municipality and arrival hour tells you the diagnosis without finding the row.
- **Informed attacker.** This attacker knows four facts about every one of the 46398 visits in `truth/health__ed_visits.csv`: the diagnosis group (icd10_primary mapped by the toolkit's `diagnosis_group`), the 10-year age band, the home municipality (shown as "other" where the release does not show it) and the arrival hour. The truth file is read locally and never copied. Singled out means exactly one released row matches all four facts. Correct means the row map of that row points at the attacker's own visit. On the protected release, 0.1282 of the attacker rows are singled out (5950 visits), and all of them are correct. With the same four facts on the original tables, 0.2501 are singled out. With exact values on the original (exact code, birth date, municipality and arrival time), 1.0 are singled out (`results/checks/informed_attacker.json`). The fix does not change this attacker, who never uses arrival_mode (`results/checks-l/informed_attacker.json`). Correct is always 1.0 here, because the attacker's facts come from the visit's own record, so a single match can only be that visit.
- **k on the joined tables.** We join ed_visits to lab_results on visit_id (130341 joined rows, 26209 visits with lab results). The key is every retained column that the field catalogue marks as a quasi-identifier or a diagnosis code: arrival_mode, arrival_ts, date_of_birth, icd10_primary, icd10_secondary, municipality and sex. k is the number of distinct visits in a group, because one visit has several lab rows. On the merged release, 0.9799 of the joined rows sit in groups of fewer than 5 visits (`results/checks/joined_k.json`). After the fix, without arrival_mode, the share is 0.9525 (`results/checks-l/joined_k.json`). Without the two diagnosis columns it is 0.2844 before the fix and 0.1459 after. So the high share comes from counting the diagnoses as part of the key; the lab columns add nothing to the key.

Scorecard before the fix: privacy 0.891, utility 0.9928, composite 0.9346 (`results/health-s1-build/scorecard.json`). After the fix: privacy 0.9533, utility 0.9928, composite 0.9709 (`results/health-s1-build-l/scorecard.json`). Every task score is unchanged, with H-U6 still at 0.9642. The scorer's k<5 share on ed_visits falls from 0.1817 to 0.0779, because arrival_mode no longer counts in its key. The other numbers in this document are from the merged release before the fix (`results/health-s1-build/`).

What this means for the research group release: anyone in the research group who knows when a patient arrived, roughly how old they are, where they live and what kind of illness they had can find that patient's row for about 1 visit in 8. That row shows the exact diagnosis codes, vital signs, lab results and outcome. With the diagnosis codes counted, almost no visit with lab results is hidden in a group of 5. So the release depends on the research environment and the agreement with a known recipient, not on k. It is not fit for public release.

TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0)
