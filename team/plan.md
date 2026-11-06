# Team plan - TrustED PETs Transformer

Working plan for the SinceAI 2026 weekend. Facts come from `../context/` and the organiser pages on sinceai.ai; roles and the demo pick are the team's to fill in.

## Schedule (Turku time, verified on the organiser pages)

| When | What |
|---|---|
| Fri 6 Nov 15:00-17:30 | Check-in and challenge selection (done: TrustED) |
| Fri 18:50-19:30 | Company briefing, TrustED experts on video, room 2067 EduCity floor 2 |
| Fri 19:30 | Full challenge opens in sinceai.app. Compare it with `../context/brief.md`; note every difference |
| Fri night | Pick dataset, sharing scenario and path (`../context/proving-ground/START_HERE.md`, "Choose your path"). Spec and tickets |
| Sat | Build. Support only on the TrustED Discord channel, no stand |
| Sat evening | Freeze scope and record the video (our own buffer: the 10:00 Sunday deadline is hard, and the vote card is built from the submission) |
| Sun 8 Nov 10:00 | Submissions close in sinceai.app. Hard deadline |
| Sun 10:00-12:00 | Builder vote (20 pairwise comparisons each on tagline, description, video, deck, tech chips) |
| Sun 10:00-13:00 | TrustED evaluates remotely |
| Sun 13:15 / 14:00 | Closing ceremony, then finals (4-minute pitch, 6 minutes of questions) |

## Roles (fill in Friday night)

| Role | Who | Owns |
|---|---|---|
| Detection | | column and free-text classification, scored with `pets-eval detect` against `metadata/field_catalog.csv` |
| Transformation | | PET per data type, the protected output, the justification against the scenario |
| Evaluation | | `pets-eval scorecard`: re-identification risk and utility before vs after, residual risks |
| Story and submission | | sharing scenario, demo, 2-minute video, sinceai.app form, deck |

## What the demo must show (from the brief, all five are required)

1. The data types identified in the original dataset.
2. The PET selected for each data type. The proving ground asks us to justify each choice against the scenario (`../context/proving-ground/START_HERE.md`).
3. The transformed dataset or the protected view.
4. Utility before vs after, as measured numbers.
5. A clear explanation of the sharing scenario the protected data is suitable for. The scorecard reports the residual risks next to it (`../context/proving-ground/START_HERE.md`).

## Judging (Since AI's criteria, evaluated remotely by TrustED)

Technical implementation (correct, reliable PET choices), innovation (intelligent, explainable approach), impact (evidence of reduced disclosure risk with preserved utility), presentation (clear scenario, before/after, honest limitations). No weighted rubric. Prizes EUR 2,000 / 750 / 250.

## Open questions for Friday night

- Which dataset and scenario? The proving ground suggests seven paths. The organisers can run hidden checks on any of them: a stronger hidden attacker per domain, the private labels of `unseen`, the hidden eval spans of `customer_service` (`../context/proving-ground/docs/EVALUATION.md`).
- Did all four register for LUMI by 30 October? If not, LUMI is out. The organisers say every challenge can be built with ordinary tools, so LUMI is optional (sinceai.ai hackathon page).
- What does the sinceai.app brief add beyond the zip?

## Lines we do not cross

- Only the synthetic proving-ground data, public data, or data we are explicitly allowed to use.
- `rowmap_*.csv` are never published (organiser rule, START_HERE.md). `truth/` and `holdout/` stay out of the repo and the zip too; that is our own caution, since they hold the answer key to the attacks.
- No claim of "anonymised", "GDPR compliant" or "differentially private" without the method and its parameters next to it.
- No fabricated numbers on any slide. Every number comes from a scorecard run we can repeat.
- No em-dash in anything shipped.
