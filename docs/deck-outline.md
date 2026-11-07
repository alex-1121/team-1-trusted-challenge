# Pitch deck outline

One line per slide: title - what it says - the one number or picture it carries (source file). Scorecard numbers are our self-assessment from the organisers' `pets-eval` and are separate from the official judging score.

1. **TrustED PETs Transformer** - one tool: detect, protect, repair, score, attack - picture: the one build command (`README.md`, "How to run").
2. **The problem** - raw emergency-department (ED) data re-identifies patients, and blanking it kills the research - number: raw linkage re-identification 0.5697 (`results/health-s1-build/summary.md`, "Before" column).
3. **The scenario: HEALTH-S1** - research group in a research environment, five analyses must still work - picture: recipient, purpose and the five tasks (`contracts/HEALTH-S1.json`). Demo item 5.
4. **The official score was wrong** - our earlier release scored composite 0.9709 with linkage 0.0, and our red team rebuilt every dropped date (share 1.0) and named 10 news-clip patients, all correctly (`results/health-s1-build/scorecard.json` at commit 7cf541b, `results/redteam/before-7cf541b.json`). Picture: visit ids in order, the hour going back, a new day.
5. **Detect: types found from values alone** - never reads column names - number: health held-out macro-F1 0.8086 against the B1 target 0.65 (`results/detect/health.json`, `results/detect/SPLIT.md`); plus 26 unseen columns labelled (`results/detect/unseen_field_labels.csv`). Demo item 1.
6. **Protect: one PET per type, with a reason** - picture: the plan table rows for token, drop, age_band, top_n_exact_else_other, hour_of_day, keep, withhold (`results/health-s1-build/plan.md`). Demo item 2.
7. **Repair only the rows at risk** - 3613 rows (0.0779) coarsened step by step until every group has k of at least 5 and 2 distinct diagnoses; all 6 step orders scored, best kept (`results/health-s1-build/repair_report.json`, `results/health-s1-build/repair_search.md`). Contrast: 20-year bands for every row drop H-U6 to 0.0271 (`results/sweep/sweep.md`).
8. **The red-team gate** - three attacks the scorecard does not run, each with a threshold; the build refuses to write `pets_submission/` when one succeeds - number: dates rebuilt 1.0 to 0.0002, patients named 10 to 0, patient fingerprint 0.3544 to not applicable (`results/redteam/before-7cf541b.json`, `results/redteam/after.json`). Demo item 3.
9. **Before and after** - privacy 0.1716 to 1.0, utility 1.0 to 0.9666, composite 0.2752 to 0.9845; per task H-U4 0.8744, the rest at or above 0.96 (`baseline-scores/health_HEALTH-S1_research-env_raw.json`, `results/health-s1-build/scorecard.json`); organiser B2-k utility 0.40 for contrast (`data/proving-ground/docs/BENCHMARK.md`). Demo item 4.
10. **Honest limits** - an attacker who already knows a visit's diagnosis group, age band, municipality and hour singles out 0.0981 of visits (`results/checks/informed_attacker.json`); exact diagnosis codes on the lab join leave 0.9521 of joined rows in groups under 5 (`results/checks/joined_k.json`); no dates, no seasonality; for a trusted research environment, not public release (`docs/guarantee-and-residual-risk.md`). Footer: "TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0)".
11. **Where this goes** - a release gate for any data leaving a company: contract as code, compile, attack, repair, receipt. Vision slide, no numbers.

## Five tech chips for the submission form

Python, pandas, HMAC-SHA256, k-anonymity and l-diversity, pets-eval.
