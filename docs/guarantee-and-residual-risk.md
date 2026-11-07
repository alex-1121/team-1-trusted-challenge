# HEALTH-S1: what we guarantee, what we do not, and which attacks we ran

Scenario HEALTH-S1: a hospital gives its emergency-department (ED) visits and lab results to a university research group in a research environment (a known recipient, no public release) (`contracts/HEALTH-S1.json`). Every number below is followed by the file it comes from. Scorecard numbers are our self-assessment from the organisers' `pets-eval`, not the official judging score.

## What changed from the release on main at 7cf541b, and why

Our own red team broke the earlier release, although the organisers' scorecard gave it composite 0.9709 and linkage re-identification 0.0 (`results/redteam/before-7cf541b.json`, built by main's own code):

- **The dropped date came back.** The release kept only the hour of arrival, but the visits could be put back in arrival order three ways: the file's own row order (dates rebuilt for 0.9975 of rows), sorting by `visit_id`, which was kept as is and is sequential (1.0), and the first `lab_results.lab_id` per visit (1.0 of the 26209 visits with labs). Wherever the hour goes backwards a new day starts, so every date returns.
- **News clips then name patients.** With the rebuilt dates, 10 of the 220 shipped news clips single out one visit, and all 10 are the right patient, so the clip's reader learns that patient's diagnosis (share 0.0455).
- **The patient pseudonym made a fingerprint.** It linked every visit of a patient; age band, sex, municipality and the set of arrival hours were unique for 0.3544 of all patients and 0.8464 of the 9885 patients with more than one visit.

The fixes are in the guarantees below. The red-team gate now runs in every build and blocks `pets_submission/` when an attack succeeds (`src/pets_transformer/redteam.py`).

## What we guarantee

Each line is a method with its parameters, applied by `protect` from `contracts/HEALTH-S1.json`. The per-column table is `results/health-s1-build/plan.md`.

- **No order in the release.** `visit_id` (in both tables) and `lab_results.lab_id` are replaced by keyed tokens: a prefix ("V", "L") plus the first 16 hex characters of HMAC-SHA256 under a 32-byte random key. The same visit gets the same token in both tables, so the visit-to-lab join (H-U7) still works, but a token says nothing about order. Both tables are written in a random row order drawn from the operating system's cryptographic source, and the row maps follow. Red team after the fix: dates rebuilt for 0.0002 of rows (file order), 0.0002 (sorted by `visit_id`), 0.0003 (first `lab_id` per visit), against a gate of 0.05 (`results/redteam/after.json`).
- **No person key.** `patient_hetu` is dropped. No HEALTH-S1 task needs it: H-U6 reads `readmit_30d` and scores 0.9641 (`results/health-s1-build/scorecard.json`). The price: researchers cannot link a patient's visits themselves.
- **k of at least 5 and l of at least 2 on every released row.** k is the size of the smallest group of rows sharing the same quasi-identifier values (a quasi-identifier identifies someone only in combination with others); l is the number of distinct primary diagnoses in that group. Columns: age band (`date_of_birth`, copied to `age`), sex, municipality, arrival hour. Scorer: k<5 share 0.0, min k 5, median k 28, 2681 groups over 46398 rows (`results/health-s1-build/scorecard.json`). Our l-diversity check: no group with fewer than 2 distinct diagnoses; the worst group has 6 rows and 2 diagnoses (`results/checks/l_diversity.json`).
- **Only the rows at risk were coarsened.** Before the repair, 3613 rows (0.0779) were in a group with k<5 or l<2. The repair coarsened only those, step by step, re-measuring after each step: 3613 rows got a 20-year age band, then 2458 still at risk got municipality "other", then 125 got a 3-hour arrival block, and the last 28 had all four columns suppressed. No row was dropped (`results/health-s1-build/repair_report.json`). The order of the steps was chosen by scoring all 6 orders with the organisers' scorecard (`results/health-s1-build/repair_search.md`).
- **Hour of day only, dates gone.** `arrival_ts` keeps "HH:00" (a 3-hour block on 125 rows, "suppressed" on 28).
- **Listed columns dropped.** From ed_visits: patient_hetu, patient_name, phone, home_address, postcode, arrival_mode, ambulance_unit, chief_complaint, attending_physician_id, attending_physician_name, discharge_ts. From lab_results: sampled_ts (`results/health-s1-build/plan.md`).
- **Two tables withheld.** clinical_notes (free text with identifying detail, no task uses it, no redactor in scope) and published_weekly_stats (a second linkage path, no task uses it) are not written at all (`contracts/HEALTH-S1.json`).
- **No direct identifier pattern left.** The organisers' regex scan found no residual direct identifiers in the 7 files of the output (`results/health-s1-build/check.txt`). The scan finds identifier formats, not every identifying fact.

## What we do not guarantee

- **An attacker who already knows the diagnosis.** An attacker who knows a visit's diagnosis group, age band, municipality and arrival hour singles out exactly one released row for 0.0981 of the 46398 visits, and 0.9292 of those are the right visit (`results/checks/informed_attacker.json`). The row then shows the vital signs, lab values, length of stay and outcome. On the original tables the same four facts single out 0.2501. Making the diagnosis group part of the k key would put most rows at risk (a scratch run, not committed) and wipe out the diagnosis-mix and lab tasks, so we did not.
- **Joined tables and exact diagnosis codes.** Joining ed_visits to lab_results and counting the exact diagnosis codes in the key, 0.9521 of the joined rows sit in groups of fewer than 5 visits; over the quasi-identifiers alone it is 0.0978, because only the 26209 visits with labs are in the join (`results/checks/joined_k.json`).
- **Clinical values are kept as they are.** Diagnosis codes, vital signs and lab values are released unchanged because the study needs them.
- **Attackers we did not build.** The scorer ran its shipped attacker files; our red team adds the order attack, news-clip linkage with rebuilt dates and the person fingerprint. A stronger attacker with other outside data was not tested.
- **The linkage attacker and age bands.** The scorer's linkage attacker reads `date_of_birth` as a date, and a band such as "30-39" does not parse as one. Our news-clip linkage does match age bands and finds 0 patients (`results/redteam/after.json`).
- **No dates, so no seasonality.** A researcher cannot study weekly or seasonal patterns on this release.
- **The key is per output folder.** A rerun into the same `out/` folder reuses the key, so tokens stay the same across those runs.

So the release depends on the research environment and the agreement with a known recipient, as HEALTH-S1 assumes. It is not fit for public release.

## Scores

| Number | Raw (`baseline-scores/health_HEALTH-S1_research-env_raw.json`) | Main at 7cf541b | This release (`results/health-s1-build/scorecard.json`) |
|---|---|---|---|
| Privacy | 0.1716 | 0.9533 | 1.0 |
| Utility | 1.0 | 0.9928 | 0.9666 |
| Composite | 0.2752 | 0.9709 | 0.9845 |
| Scorer k<5 share, ed_visits | 1.0 | 0.0779 | 0.0 |
| H-U4 diagnosis mix, top 8 municipalities | 1.0 | 1.0 | 0.8744 |
| H-U8 hour-of-day curve | 1.0 | 1.0 | 0.9945 |
| Red-team gate | - | fail | pass |

Main at 7cf541b: `results/health-s1-build/scorecard.json` at commit 7cf541b and `results/redteam/before-7cf541b.json`. The utility cost sits in H-U4: 2458 at-risk rows lost their municipality. Every other task stayed at or above 0.96.

TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0)
