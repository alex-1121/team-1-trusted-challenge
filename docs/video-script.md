# Demo video script

Spoken English, about two and a half minutes, read by us in first person plural. Lines in square brackets are screen cues and are not spoken.

The paste-ready text for the voiceover tool is `docs/video-voiceover.txt`: the spoken lines only, one paragraph each, decimals written as words and the product name spelled Trusted so it is read as one word. Redo that file after any change to a spoken line here.

[title card]

A hospital wants to share emergency room records with researchers. TrustED protects the data before it leaves, picks each column's protection by measuring, and refuses a release that an attack breaks.

[results/detect/health.json]

It reads each column and labels it: does it name a person, or only help pick someone out? On the hospital test tables three in four labels are right.

[contracts/HEALTH-S1.json]

Then it tries every way to hide a column: drop it, keep only the hour or the month, swap names for codes. A way passes if the researchers' five questions still get their answers and under 5 percent of visits sit in a group of fewer than five lookalikes. It keeps the most useful way that passes. Date plus hour exposes almost every visit, so it keeps the hour.

[demo/the-er-register.html]

Names and phone numbers go, visit numbers become keyed codes, rows are shuffled, and the 3,746 visits still easy to pick out are coarsened until every group has at least five.

[results/health-s1-build/summary.md]

All 46,398 visits stay in. On the organisers' scorer, against its own attackers, privacy rises from 0.17 to 1.0 and usefulness drops from 1.0 to 0.97.

[results/redteam/before-7cf541b.json]

We attacked our own earlier release. Row order gave back almost every hidden date, and 10 of 220 news reports named the right patient. Keyed codes and shuffled rows fixed that. Now no attack works, and one that did would stop the release.

[policy/HEALTH-S1.policy.json and its signature, then the build refusing after one threshold is changed]

The hospital's data steward signs the policy that sets the risk limits. Change one number and the build stops.

[results/detect-semantic/e2_eu_test.json]

Our word lists know Finnish names, so a German surname looks harmless to them. A small language model on the laptop catches those, and no data leaves it. On fake Czech tables it never saw, letting it label raised the score from 0.60 to 0.77. Today it only flags columns for a person to check, and on those tables all 28 flags were real mistakes. The build does not wait for that check. Both the word lists and the model come from made-up data, so a real hospital would rebuild the lists and retrain the model on its own data first.

[results/health-s1-build/checks/informed_attacker.json]

Still open: knowing a visit's diagnosis group, age range, town and hour singles out one visit in ten, 93 percent correctly. Our detector also mislabels triage, how urgent a visit is, as plain, so we count it as known, and then 15 percent of visits stand out. The signature shows which policy was used. Two releases that each pass on their own can still be combined by whoever holds both, until people stand out again. We do not test for that. Today only a secure processing room and a data-use agreement forbid it. Nobody independent has checked our work. These scores are our own, separate from official judging.

[attribution card: TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0)]

## Sources of the spoken numbers

- About three in four labels right (accuracy 0.7358, 53 columns over the four health tables): `results/detect/health.json`.
- Five questions (required tasks H-U2, H-U4, H-U6, H-U7, H-U8): `contracts/HEALTH-S1.json` (required_tasks), `results/health-s1-build/summary.md`.
- Fewer than five lookalikes (k 5): `contracts/HEALTH-S1.json` (fitness block, k).
- Under 5 percent (risk_line 0.05): `contracts/HEALTH-S1.json`, `results/selection/HEALTH-S1.v2.json` (arrival_ts entry).
- Date plus hour exposes almost every visit (risk 0.999), hour of day chosen (risk 0.0227): `results/selection/HEALTH-S1.v2.json` (arrival_ts entry), `contracts/HEALTH-S1.json` (arrival_ts reason).
- Names and phone numbers dropped, visit numbers keyed tokens, rows shuffled: `contracts/HEALTH-S1.json` (column rules), `README.md` ("protect writes the release with the chosen order (tokens, shuffled rows, repair)").
- 3,746 visits coarsened until every group has at least five (at_risk_before 3746, at_risk_after 0): `results/health-s1-build/repair_report.json`.
- 46,398 visits: `contracts/HEALTH-S1.json` (fitness, ed_visits n_rows), `results/health-s1-build/repair_report.json` (rows, rows_released).
- Privacy 0.17 raw (0.1716), usefulness 1.0 raw: `baseline-scores/health_HEALTH-S1_research-env_raw.json`.
- Privacy 1.0, usefulness 0.97 (0.971), against the scorer's own attackers only: `results/health-s1-build/scorecard.json`, `results/health-s1-build/summary.md` ("the toolkit's shipped attackers only").
- Almost every hidden date returns from row order (file order 0.9975; 1.0 sorted by visit_id), 10 of 220 reports name the right patient: `results/redteam/before-7cf541b.json`.
- No attack works (all five pass, gate pass; dates rebuilt 0.0003, reports 0.0): `results/health-s1-build/redteam.json`.
- Signed policy sets the risk limits, build stops when a threshold changes: `policy/HEALTH-S1.policy.json` and its signature, `plans/2026-11-07-release-gate.md`.
- Label score 0.60 to 0.77 on Czech tables is macro-F1 (0.5963 to 0.7709), word lists alone then word lists plus model labelling (hybrid mode, test split run once on commit 68aa116); the detector line above uses accuracy, so the two are not comparable: `results/detect-semantic/e2_eu_test.json`, `results/detect-semantic/SPLIT.md`.
- 28 flags, all real mistakes, on the locked fake EU tables only (advisor mode, `eu_locked`): `results/detect-semantic/advisor.json`. On the hospital tables the same advisor raised 7 flags, 3 real and 4 false alarms; over the three held-out proving-ground datasets 11 flags, 5 real (`datasets.health`, `datasets.public_admin`, `datasets.customer_service` in the same file).
- One visit in ten (0.0971), 93 percent of them correctly (0.9294): `results/health-s1-build/checks/informed_attacker.json`.
- Triage a detector error (catalogue sensitive_attribute, predicted non_sensitive): `results/detect/health.json` (errors). 15 percent after the repair (0.1547, line not met): `contracts/HEALTH-S1.json` (triage and arrival_ts reasons).
- Attribution wording: `AGENTS.md`.
- The three spoken limitations (releases combined, review flag does not stop the build, word lists and model from made-up data): `context/proving-ground/docs/LIMITATIONS.md`.

Numbers are rounded for speech. The scorecard is our own self-assessment and is separate from the official judging score. The 0.60 to 0.77 score is from the model labelling on its own (hybrid mode); the shipped default is advisor mode, where it only flags.

<!-- spoken words: 457 (counted without the heading, the intro line, screen cues and the sources section) -->
