# Pitch deck outline

One line per slide: title - what it says - the one number or picture it carries (source file). Scorecard numbers are our self-assessment from the organisers' `pets-eval` and are separate from the official judging score.

1. **TrustED PETs Transformer** - one tool: detect, protect, score - picture: the one build command (`README.md`, "How to run").
2. **The problem** - raw emergency-department (ED) data re-identifies patients, and blanking it kills the research - number: raw linkage re-identification 0.5697 (`results/health-s1-build/summary.md`, "Before" column).
3. **The scenario: HEALTH-S1** - research group in a research environment, five analyses must still work - picture: recipient, purpose and the five tasks (`contracts/HEALTH-S1.json`). Demo item 5.
4. **Detect: types found from values alone** - never reads column names - number: health held-out macro-F1 0.8086 (F1 per privacy role, averaged; 1.0 is perfect) against the B1 target 0.65 (`results/detect/health.json`, `results/detect/SPLIT.md`); plus 26 unseen columns labelled (`results/detect/unseen_field_labels.csv`). Demo item 1.
5. **Protect: one PET per type, with a reason** - picture: seven rows of the plan table, one per PET: pseudonym (a keyed stand-in code, the same patient always gets the same one), age_band, top_n_exact_else_other, hour_of_day, drop, keep, withhold (`results/health-s1-build/plan.md`). Demo item 2.
6. **The protected output** - two tables plus row maps, no data file in the repo - number: 46398 ed_visits rows kept, no residual direct identifiers in 6 scanned files (`results/health-s1-build/scorecard.json`, `results/health-s1-build/check.txt`). Demo item 3.
7. **Utility before and after** - picture: five tasks before and after, H-U6 0.9642, the rest 1.0; utility 1.0 to 0.9928 (`baseline-scores/health_HEALTH-S1_research-env_raw.json`, `results/health-s1-build/scorecard.json`); organiser B2-k utility 0.40 for contrast (`data/proving-ground/docs/BENCHMARK.md`). Demo item 4.
8. **Privacy before and after** - number: privacy 0.1716 to 0.9533, composite 0.2752 to 0.9709 (`baseline-scores/health_HEALTH-S1_research-env_raw.json`, `results/health-s1-build/scorecard.json`).
9. **Why these parameters** - picture: the sweep table; 20-year bands drop H-U6 to 0.0271, 2-hour blocks drop H-U8 to 0.0, 10-year bands with 1-hour blocks win at composite 0.9709 (`results/sweep/sweep.md`).
10. **Honest limits** - number: k<5 share 0.0779 (k counts the rows sharing one combination of quasi-identifiers, columns such as age band and municipality that identify someone only in combination; k-anonymity at 5 means every such group holds at least 5 rows), so the k of at least 5 target is not met for every row; dropping arrival_mode, the l-diversity finding, is what brought it down; shipped attackers only; no dates, no seasonality; linkage 0.0 may be optimistic (`results/health-s1-build/summary.md`, `results/health-s1-gate/GATE.md`, `docs/guarantee-and-residual-risk.md`). Footer: "TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0)".

## Five tech chips for the submission form

Python, pandas, HMAC-SHA256, k-anonymity, pets-eval.
