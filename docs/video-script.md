# Demo video script

Spoken English, about two minutes, read by us in first person plural. Lines in square brackets are screen cues and are not spoken.

[demo/the-er-register.html]

A hospital wants to share emergency room records with researchers. TrustED protects that data before it leaves. It picks each column's protection itself, by measuring, and refuses to release data that an attack breaks.

[results/detect/health.json]

It reads each column, like birth date or town, and labels what it holds.

[contracts/HEALTH-S1.json]

Then it tries every way to hide a column: drop it, keep the hour or the month only, or swap names for codes. It asks two things. Do the researchers' five questions still get nearly the same answers? And do under 5 percent of visits stand out, meaning fewer than five visits look alike? It keeps the most useful option that passes. Date plus hour exposes almost every visit, so it keeps the hour.

[results/health-s1-build/summary.md]

All 46,398 visits stay in. On the hackathon organisers' scorer, privacy rises from 0.17 to 1.0, and usefulness drops from 1.0 to 0.97.

[results/redteam/before-7cf541b.json]

Our red team, teammates attacking our own data, broke an earlier release. Row order gave back almost every hidden date, and 10 of 220 news reports named the right patient. Now any attack that works stops the release, and all five fail.

[results/detect-semantic/e2_eu_test.json]

It also works beyond Finnish data. Our word lists know Finnish names, so a German surname looks harmless to them. A small language model on the laptop catches those, and no data leaves it. On fake Czech tables, unseen in training, its label score rose from 0.60 to 0.77 out of 1, and no name or address passed as harmless.

[results/detect-semantic/advisor.json]

Today the word lists still decide; the model flags columns for a person to check. On those tables, all 28 flags were real mistakes. It still raises false alarms, and more and better training data improves it.

[results/health-s1-build/checks/informed_attacker.json]

What is still open: knowing a visit's diagnosis group, age range, town and hour singles out about one visit in ten, 93 percent correctly. Triage, how urgent a visit is, stays for the study, and with it 15 percent of visits stand out. These scores are our self-assessment, separate from official judging.

## Sources of the spoken numbers

- Five questions (required tasks H-U2, H-U4, H-U6, H-U7, H-U8): `contracts/HEALTH-S1.json` (required_tasks), `results/health-s1-build/summary.md`.
- Fewer than five visits look alike (k 5): `contracts/HEALTH-S1.json` (fitness block, k).
- Under 5 percent of visits stand out (risk_line 0.05): `contracts/HEALTH-S1.json`, `results/selection/HEALTH-S1.v2.json` (arrival_ts entry).
- Date plus hour exposes almost every visit (risk 0.999), hour of day chosen (risk 0.0227): `results/selection/HEALTH-S1.v2.json` (arrival_ts entry), `contracts/HEALTH-S1.json` (arrival_ts reason).
- 46,398 visits: `contracts/HEALTH-S1.json` (fitness, ed_visits n_rows), `results/health-s1-build/checks/informed_attacker.json` (n_attacker_rows).
- Privacy 0.17 raw (0.1716), usefulness 1.0 raw: `baseline-scores/health_HEALTH-S1_research-env_raw.json`.
- Privacy 1.0, usefulness 0.97 (0.971): `results/health-s1-build/scorecard.json`.
- Almost every date returns from row order (file order 0.9975; 1.0 sorted by visit_id), 10 of 220 news reports name the right patient (news_linkage: clips 220, correct 10): `results/redteam/before-7cf541b.json`.
- Any working attack stops the build; all five attacks fail (gate pass; dates rebuilt 0.0002, clips 0.0): `results/health-s1-build/redteam.json`; gate rule in `README.md` (build section) and `plans/2026-11-07-release-gate.md`.
- Label score 0.60 to 0.77 out of 1 on the Czech tables (macro-F1, cs_CZ word lists 0.5963, hybrid 0.7709; Czech is a country the model never trained on), no name or address column labelled harmless (hybrid model_types harmless 0 in cs_CZ, pt_PT and hu_HU): `results/detect-semantic/e2_eu_test.json`. Test split run once on commit 68aa116, before the review fixes (`results/detect-semantic/SPLIT.md`).
- Word lists still decide (all_labels_equal_lexicon true), all 28 flags right on the fake EU test tables (eu_locked: flags 28, catches 28, false_alarms 0), false alarms remain (proving_ground_held_out: false_alarms 6 of 11 flags): `results/detect-semantic/advisor.json`.
- About one visit in ten (0.0971), 93 percent correctly (0.9294): `results/health-s1-build/checks/informed_attacker.json`.
- Triage stays, 15 percent stand out with it (0.1547, line not met after repair): `contracts/HEALTH-S1.json` (triage and arrival_ts reasons).

Numbers are rounded for speech. The scorecard is our own self-assessment and is separate from the official judging score.

<!-- spoken words: 336 (counted without the heading, the intro line, screen cues and this section) -->
