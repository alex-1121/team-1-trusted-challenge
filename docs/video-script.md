# Demo video script (under 2 minutes)

English narration, first person plural, about 260 spoken words. Screen cues are in brackets and are not spoken. Every number is followed, below the script, by the file it comes from.

## Script

**The problem (10 s)**

[Title card: TrustED PETs Transformer]

Hospitals hold data researchers need. Handing it over as it is exposes patients. Blanking everything kills the research.

**The scenario (10 s)**

[Contract file contracts/HEALTH-S1.json on screen]

Our scenario is HEALTH-S1. A university research group studies crowding and revisits in an emergency department. Five analyses must still work.

**The tool's three verbs (50 s)**

[Terminal: python -m pets_transformer.cli build --scenario HEALTH-S1]

One command runs three steps.

[Label file scrolling, then the detector score table]

Detect. The tool labels every column from its values alone. It never reads column names. On the health tables it never saw while tuning, it scores macro-F1 0.81 against the organisers' labels.

[plan.md table, highlight patient_hetu, date_of_birth, arrival_ts, clinical_notes]

Protect. A written contract picks one technique per column, with a reason. The national id becomes a keyed HMAC pseudonym, so revisits still link. Birth dates become ten-year age bands. Arrival time keeps only the hour. Names, phones, addresses and postcodes are dropped. Lab results keep their visit link, so the lab analysis still joins. Clinical notes are not released at all.

[pets_submission/health folder, then check.txt]

Score. The organisers' scorecard and identifier scan run on the result. The scan finds no direct identifiers left.

**Before and after (25 s)**

[scorecard.html, before and after columns]

Before, privacy is 0.17. After, it is 0.89. Utility moves from 1.0 to 0.99. Four of five tasks are perfect, the revisit task scores 0.96. The composite rises from 0.28 to 0.93. The organisers' k-anonymity baseline keeps only utility 0.40 here.

**Honest limits (15 s)**

[Residual-risk paragraph from summary.md]

Eighteen percent of visits still sit in groups smaller than five. We tested only the shipped attackers, and the linkage attacker may not read our age bands, so its zero could be optimistic. Without dates, nobody can study seasons.

**Close (5 s)**

[Attribution card]

TrustED PETs Proving Ground 2026, synthetic data by Since AI ry, CC BY 4.0.

## Sources of the spoken numbers

- Five analyses: `contracts/HEALTH-S1.json` (required_tasks).
- macro-F1 0.81 (0.8086): `results/detect/health.json`.
- No direct identifiers left: `results/health-s1-build/check.txt`.
- Privacy 0.17 before (0.1716), utility 1.0 before, composite 0.28 before (0.2752): `baseline-scores/health_HEALTH-S1_research-env_raw.json`.
- Privacy 0.89 after (0.891), utility 0.99 after (0.9928), composite 0.93 after (0.9346), revisit task 0.96 (H-U6 0.9642): `results/health-s1-build/scorecard.json`.
- Baseline utility 0.40 (B2-k): `data/proving-ground/docs/BENCHMARK.md` (organiser file in the restored proving ground).
- Eighteen percent (k<5 share 0.1817) and the linkage zero (0.0): `results/health-s1-build/summary.md`; why it may be optimistic: `results/health-s1-gate/GATE.md`.

Numbers are rounded for speech; the screen shows the full values. The scorecard is our self-assessment, not the official judging score.
