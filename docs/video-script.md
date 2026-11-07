# Demo video script (under 2 minutes)

English narration, first person plural, about 260 spoken words. Screen cues are in brackets and are not spoken. Every number is followed, below the script, by the file it comes from.

## Script

**The problem (10 s)**

[Title card: TrustED PETs Transformer, then `demo/the-er-register.html`: the raw sheet of patient records]

Hospitals hold data researchers need. Hand it over as it is and you expose patients. Blank everything and the research dies.

**The twist: the official score was wrong (25 s)**

[results/redteam/before-7cf541b.json next to the earlier scorecard]

Our first release scored 0.97 on the organisers' scorecard, with linkage risk zero. Then we attacked it ourselves. We had dropped the arrival date and kept only the hour. But the visit numbers run in arrival order. Sort by them, start a new day whenever the hour goes back, and every date returns. With those dates, ten patients from local news were named, each one correctly, with their diagnosis.

**The tool (50 s)**

[Terminal: python -m pets_transformer.cli build --scenario HEALTH-S1]

So now the tool picks its own protection and attacks its own output before anything ships. One command.

[Detector labels]

[`demo/the-er-register.html`: the blue scan redacts the sheet]

Detect. It labels every column from its values alone, macro-F1 0.82 on the held-out health tables.

[contracts/HEALTH-S1.json, one reason line]

Select. For each column it tries techniques from most private to least, and keeps the first one the research still works with. Arrival time: month, week, both break the arrival curve, hour of day keeps it. Sex, most vital signs and the notes go, because no analysis needs them.

[repair_search.md]

Protect and repair. Visit numbers become keyed tokens, rows are shuffled. Then only the rows still at risk are coarsened, until every group has at least five visits and two diagnoses.

[results/health-s1-build/redteam.json: gate pass]

Attack. Five attacks run again. Dates rebuilt: zero. Patients named: zero. Only then is the release written. Keep a patient key, as the organisers suggest, and the gate refuses: a third of patients are unique by their visit pattern.

**Before and after (20 s)**

[scorecard.html]

Privacy goes from 0.17 raw to 1.0. The composite rises from 0.28 to 0.99, above our earlier 0.97, and now the number holds up. The same command protects the data for an AI vendor and an education vendor without a single hand-written rule.

**Honest limits (10 s)**

[docs/guarantee-and-residual-risk.md]

Someone who already knows a patient's diagnosis can still find one visit in ten. This release is for a trusted research environment, not for the public.

**Close (5 s)**

[`demo/the-er-register.html`: the folded release is addressed, postmarked and sent; end card. Then the attribution card]

TrustED PETs Proving Ground 2026, synthetic data by Since AI ry, CC BY 4.0.

## Sources of the spoken numbers

- Earlier release 0.97 (composite 0.9709), linkage zero: `results/health-s1-build/scorecard.json` at commit 7cf541b.
- Every date returns (share_rows_date_rebuilt 1.0), ten patients named correctly (10 of 220 clips): `results/redteam/before-7cf541b.json`.
- macro-F1 0.82 (0.8202): `results/detect/health.json`. Not a clean held-out score: the wide-sample rule was narrowed after seeing held-out results (`results/detect/RESULTS.md`).
- Month and week break the arrival curve (H-U8 0.0), hour of day keeps it (1.0): `contracts/HEALTH-S1.json` (arrival_ts reason), `results/selection/HEALTH-S1.json`.
- At least five visits and two diagnoses per group: `results/health-s1-build/scorecard.json` (min k 5), `results/health-s1-build/checks/l_diversity.json`.
- Dates rebuilt zero (0.0002), patients named zero: `results/health-s1-build/redteam.json`.
- A third of patients unique with a patient key (0.2935): `results/health-s1-pseudonym-build/redteam.json`.
- Privacy 0.17 raw (0.1716), composite 0.28 raw (0.2752): `baseline-scores/health_HEALTH-S1_research-env_raw.json`.
- Privacy 1.0, composite 0.99 (0.9866): `results/health-s1-build/scorecard.json`.
- AI vendor and education vendor: `results/health-s3-build/`, `results/edu-s2-build/`.
- One visit in ten (0.0971): `results/health-s1-build/checks/informed_attacker.json`; closed at composite 0.9647 by `contracts/HEALTH-S1-informed.json` (`results/health-s1-informed-build/`).

Numbers are rounded for speech; the screen shows the full values. The scorecard is our own self-assessment and is separate from the official judging score.
