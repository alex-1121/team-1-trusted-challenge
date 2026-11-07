# Demo video script

Spoken English, about two minutes, read by us in first person plural. Lines in square brackets are screen cues and are not spoken.

[demo/the-er-register.html]

A hospital wants to give its emergency visits and lab results to a university research group. Our tool decides what it can send.

[results/detect/health.json]

It reads each column's values and labels what it holds, like a birth date or a diagnosis. On a hospital test table it scores 0.82 out of 1, so some labels are wrong.

[contracts/HEALTH-S1.json]

For each column it tries every option and measures two things on the data: do the researchers' five questions still work, and how many visits sit in a group of fewer than five lookalikes. It keeps the most useful option under a line we set at 5 percent. Date plus hour of arrival is far over that line, so it keeps the hour only. For age, town and arrival time it chose what we had chosen by hand.

[results/health-s1-build/summary.md]

All 46,398 visits stay in. On the organisers' scorer privacy goes from 0.17 to 1.0 and usefulness from 1.0 to 0.97. This is our self-assessment, separate from the official judging.

[results/redteam/before-7cf541b.json]

Our red team broke our earlier release. Row order gave almost every dropped date back, and 10 of 220 news clips then named the right patient. Now all five attacks fail.

[results/health-s1-build/checks/informed_attacker.json]

What we have not solved: someone who knows a visit's diagnosis group, age band, town and hour singles out about one visit in ten, 93 percent of them correctly. Our detector calls triage, how urgent a visit is, a plain value. It stays because the study needs it, and with triage known 15 percent of visits sit in small groups, above our line. If someone knows every value we kept, all visits do. So it only fits a research environment with a known recipient.

## Sources of the spoken numbers

- macro-F1 0.82 (0.8202): `results/detect/health.json`. Not a clean held-out score: the wide-sample rule was narrowed after seeing held-out results (`results/detect/RESULTS.md`), so the script says "test table" and makes no held-out claim.
- Five questions (required tasks H-U2, H-U4, H-U6, H-U7, H-U8): `contracts/HEALTH-S1.json` (required_tasks), `results/health-s1-build/summary.md`.
- Groups of fewer than five (k 5): `contracts/HEALTH-S1.json` (fitness block, k).
- The line at 5 percent (risk_line 0.05): `contracts/HEALTH-S1.json`, `results/selection/HEALTH-S1.v2.json` (arrival_ts entry).
- Date plus hour far over the line (risk 0.999), hour of day chosen (risk 0.0227): `results/selection/HEALTH-S1.v2.json` (arrival_ts entry), `contracts/HEALTH-S1.json` (arrival_ts reason).
- Same picks as by hand for age, town, arrival time (no number spoken): `contracts/HEALTH-S1.json` against `contracts/HEALTH-S1.handwritten.json` (age_band, top_n_exact_else_other, hour_of_day in both).
- 46,398 visits: `contracts/HEALTH-S1.json` (fitness, ed_visits n_rows), `results/health-s1-build/checks/informed_attacker.json` (n_attacker_rows).
- Privacy 0.17 raw (0.1716), usefulness 1.0 raw: `baseline-scores/health_HEALTH-S1_research-env_raw.json`.
- Privacy 1.0, usefulness 0.97 (0.971): `results/health-s1-build/scorecard.json`.
- Almost every date returns from row order (file order 0.9975; 1.0 sorted by visit_id), 10 of 220 clips name the right patient: `results/redteam/before-7cf541b.json`.
- All five attacks fail (gate pass; dates rebuilt 0.0002, clips 0.0): `results/health-s1-build/redteam.json`.
- One visit in ten (0.0971), 93 percent of them correctly (0.9294): `results/health-s1-build/checks/informed_attacker.json`.
- Triage labelled plain (non_sensitive CATEGORY), 15 percent after the repair (0.1547, line not met): `contracts/HEALTH-S1.json` (triage and arrival_ts reasons).
- All visits in small groups once every kept value is known (share_k_below_5 1.0): `contracts/HEALTH-S1.json` (fitness, ed_visits).

Numbers are rounded for speech. The scorecard is our own self-assessment and is separate from the official judging score.

<!-- spoken words: 279 (counted without the heading, the intro line, screen cues and this section) -->
