# HEALTH-S1: what we guarantee, what we do not, and which attacks we ran

Scenario HEALTH-S1: a hospital gives its emergency-department (ED) visits and lab results to a university research group in a research environment (a known recipient, no public release) (`contracts/HEALTH-S1.json`). Every number below is followed by the file it comes from. Scorecard numbers are our self-assessment from the organisers' `pets-eval`, not the official judging score.

## Why the earlier release was replaced

Our own red team broke the release on main at commit 7cf541b, although the organisers' scorecard gave it composite 0.9709 and linkage re-identification 0.0 (`results/redteam/before-7cf541b.json`, built by main's own code):

- **The dropped date came back.** The release kept only the hour of arrival, but the visits could be put back in arrival order three ways: the file's own row order (dates rebuilt for 0.9975 of rows), sorting by `visit_id`, which was kept as is and is sequential (1.0), and the first `lab_results.lab_id` per visit (1.0 of the 26209 visits with labs). Wherever the hour goes backwards a new day starts, so every date returns.
- **News clips then name patients.** With the rebuilt dates, 10 of the 220 shipped news clips single out one visit, and all 10 are the right patient, so the reader of the clip learns that patient's diagnosis.
- **The patient pseudonym made a fingerprint.** It linked every visit of a patient; age band, sex, municipality and the set of arrival hours were unique for 0.3544 of all patients and 0.8464 of the 9885 patients with more than one visit.
- **The organisers' linkage attacker could not see it.** It reads a column named `date_of_birth` as a date, so an age band such as "30-39" gives it no age, and it reads "HH:00" as today's date, so its time window matches nothing.

## What we guarantee

Each line is a method with its parameters, applied from `contracts/HEALTH-S1.json`, which the selector wrote (`results/selection/HEALTH-S1.json`). The per-column table is `results/health-s1-build/plan.md`.

- **Only what a required task needs is released.** The selector tried every column with a ladder of candidates, most private first, and kept the first one under which all five required tasks stay within 0.05 of a release with exact values. Released from ed_visits: visit token, 10-year age band (also as `age`), municipality (8 most common, the rest "other"), arrival hour, triage, primary diagnosis, temperature, length of stay, 30-day readmission flag. From lab_results: visit token, test code, value. Everything else is dropped, including sex, the other vital signs, the secondary diagnosis and disposition; clinical_notes and published_weekly_stats are withheld (`contracts/HEALTH-S1.json`).
- **No direct identifier, no person key.** The national id, name, phone, address, physicians and free text are dropped. No patient pseudonym is released, so visits of one patient cannot be linked; H-U6 reads `readmit_30d` and scores 0.9579 (`results/health-s1-build/scorecard.json`).
- **No order in the release.** `visit_id` in both tables is a keyed token: "T" plus the first 16 hex characters of HMAC-SHA256 under a 32-byte key drawn fresh for every build, never released. The same visit gets the same token in both tables, so the lab join (H-U7 1.0) works, but a token says nothing about order, and tokens of two builds cannot be joined. Both tables are written in a random row order from the operating system's cryptographic source. Red team: dates rebuilt for 0.0002 of rows (`results/health-s1-build/redteam.json`).
- **k of at least 5 and l of at least 2 on every row, also among visits with labs.** k is the number of rows sharing the same quasi-identifier values (a quasi-identifier identifies someone only in combination); l is the number of distinct primary diagnoses in that group. Columns: age band, municipality, arrival hour, plus whether the visit has lab results, because the release shows it. Scorer: k<5 share 0.0, min k 5, median k 55, 1691 groups over 46398 rows (`results/health-s1-build/scorecard.json`). l-diversity: no group with fewer than 2 distinct diagnoses (`results/health-s1-build/checks/l_diversity.json`). Joined with lab results, over the quasi-identifiers, no visit sits in a group of fewer than 5 visits (`results/health-s1-build/checks/joined_k.json`).
- **Only the rows at risk were coarsened.** 3746 rows (0.0807) missed the target after protection. They got a 20-year age band; 2584 still at risk got a 3-hour arrival block; 589 got municipality "other"; the last 60 had the three columns suppressed; no row was dropped (`results/health-s1-build/repair_report.json`). The step order was chosen by scoring all 6 orders (`results/health-s1-build/repair_search.md`).
- **The organisers' own attacker, made band-aware, finds nothing.** Rerun with the age read from the band and the hour-only time left out (it cannot be placed on a date): re-identification 0.0 for the news clips, social posts and public directory (`results/health-s1-build/redteam.json`).
- **No plain hash and no identifier pattern.** No released value equals the MD5, SHA-1 or SHA-256 of an original value (`results/health-s1-build/redteam.json`). The organisers' regex scan found no residual direct identifiers in the 7 files of the output (`results/health-s1-build/check.txt`).

## What we do not guarantee

- **An attacker who already knows the diagnosis.** One who knows a visit's diagnosis group, age band, municipality and arrival hour singles out exactly one row for 0.0964 of the 46398 visits, 0.932 of those correctly (`results/health-s1-build/checks/informed_attacker.json`), and then sees that visit's length of stay, temperature and lab values. With the same facts on the original tables it is 0.2501. Making the diagnosis group part of the k key would put most rows at risk (a scratch run, not committed) and wipe out the diagnosis-mix and lab tasks, so we did not.
- **Exact diagnosis codes on the lab join.** Counting the exact diagnosis code in the key, 0.7063 of visits with lab results sit in groups of fewer than 5 such visits (`results/health-s1-build/checks/joined_k.json`). Diagnosis is the sensitive value, not a quasi-identifier, so k usually leaves it out; we report it for an attacker who knows the code.
- **Clinical values are released as they are.** Diagnosis, triage, temperature, length of stay and lab values are exact because the study needs them.
- **Attackers we did not build.** We ran the shipped attackers, a band-aware rerun of them, and our own order, news-clip, fingerprint and hash attacks. A stronger attacker with other outside data was not tested.
- **Tasks pay a price.** H-U8 (arrival curve) falls to 0.8769 because 2584 at-risk rows got a 3-hour block; H-U4 to 0.9611; H-U6 to 0.9579 (`results/health-s1-build/scorecard.json`). Without the lab join flag the composite would be 0.9918 instead of 0.9808, with 0.0521 of visits with labs in groups of fewer than 5 (`results/health-s1-noflag-build/`).
- **No dates, so no seasonality.** A researcher cannot study weekly or seasonal patterns on this release.
- **Not the organisers' suggested patient key.** Their suggested targets ask for a consistent pseudonymous patient key (`metadata/scenarios.json`). With one, 0.2906 of patients are unique by fingerprint and our gate refuses the release (`results/health-s1-pseudonym-build/redteam.json`).

So the release depends on the research environment and the agreement with a known recipient, as HEALTH-S1 assumes. It is not fit for public release.

## Scores

| Number | Raw | Main at 7cf541b | This release |
|---|---|---|---|
| Privacy | 0.1716 | 0.9533 | 1.0 |
| Utility | 1.0 | 0.9928 | 0.9588 |
| Composite | 0.2752 | 0.9709 | 0.9808 |
| Scorer k<5 share, ed_visits | 1.0 | 0.0779 | 0.0 |
| Red-team gate | - | fail | pass |

Sources: `baseline-scores/health_HEALTH-S1_research-env_raw.json`; `results/health-s1-build/scorecard.json` at commit 7cf541b and `results/redteam/before-7cf541b.json`; `results/health-s1-build/scorecard.json` and `results/health-s1-build/redteam.json`.

TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0)
