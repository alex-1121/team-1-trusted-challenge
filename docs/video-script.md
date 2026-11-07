# Demo video script (under 2 minutes)

English narration, first person plural, about 260 spoken words. Screen cues are in brackets and are not spoken. Every number is followed, below the script, by the file it comes from.

## Script

**The problem (10 s)**

[Title card: TrustED PETs Transformer]

Hospitals hold data researchers need. Hand it over as it is and you expose patients. Blank everything and the research dies.

**The scenario (10 s)**

[Contract file contracts/HEALTH-S1.json on screen]

Our scenario is HEALTH-S1. A university research group studies crowding and revisits in an emergency department. Five analyses must still work.

**The twist: the official score was wrong (25 s)**

[results/redteam/before-7cf541b.json next to the earlier scorecard]

Our first release scored 0.97 on the organisers' scorecard, with linkage risk zero. Then we attacked it ourselves. We had dropped the arrival date and kept only the hour. But the visit numbers run in arrival order. Sort by them, start a new day whenever the hour goes back, and every date returns. With those dates, ten patients from local news were named, each one correctly, with their diagnosis.

**The tool (40 s)**

[Terminal: python -m pets_transformer.cli build --scenario HEALTH-S1]

So the tool now attacks its own output before it ships anything. One command.

[Label file, detector score table]

Detect. It labels every column from its values alone, macro-F1 0.81 on health tables it never saw while tuning.

[plan.md table]

Protect. A contract picks one technique per column, with a reason. Visit numbers become keyed tokens, so labs still join but no order is left, and rows are shuffled. The patient code is dropped. Age becomes ten-year bands, arrival keeps only the hour.

[repair_search.md]

Repair. Only the rows still at risk are coarsened, until every group has at least five visits and two diagnoses. The tool tries every order and keeps the best score.

[results/redteam/after.json: gate pass]

Then the red team runs again. Dates rebuilt: zero. Patients named: zero. Only then is the release written.

**Before and after (20 s)**

[scorecard.html]

Privacy goes from 0.17 raw to 1.0. Utility stays at 0.97. The composite rises from 0.28 to 0.98, above our own earlier 0.97, and now the number is true.

**Honest limits (10 s)**

[docs/guarantee-and-residual-risk.md]

Someone who already knows a patient's diagnosis can still find one visit in ten. This release is for a trusted research environment, not for the public.

**Close (5 s)**

[Attribution card]

TrustED PETs Proving Ground 2026, synthetic data by Since AI ry, CC BY 4.0.

## Sources of the spoken numbers

- Five analyses: `contracts/HEALTH-S1.json` (required_tasks).
- Earlier release 0.97 (composite 0.9709), linkage zero: `results/health-s1-build/scorecard.json` at commit 7cf541b.
- Every date returns (share_rows_date_rebuilt 1.0), ten patients named correctly (10 of 220 clips): `results/redteam/before-7cf541b.json`.
- macro-F1 0.81 (0.8086): `results/detect/health.json`.
- At least five visits and two diagnoses per group: `results/health-s1-build/scorecard.json` (min k 5), `results/checks/l_diversity.json`.
- Dates rebuilt zero (0.0002), patients named zero: `results/redteam/after.json`.
- Privacy 0.17 raw (0.1716), composite 0.28 raw (0.2752): `baseline-scores/health_HEALTH-S1_research-env_raw.json`.
- Privacy 1.0, utility 0.97 (0.9666), composite 0.98 (0.9845): `results/health-s1-build/scorecard.json`.
- One visit in ten (0.0981): `results/checks/informed_attacker.json`.

Numbers are rounded for speech; the screen shows the full values. The scorecard is our own self-assessment and is separate from the official judging score.
