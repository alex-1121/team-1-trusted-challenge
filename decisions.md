# Decisions

| Date | Decision | Why | Who |
|---|---|---|---|
| 2026-11-06 | TrustED challenge chosen at the Friday selection | Team pick at the challenge selection | team |
| 2026-11-06 | Code and context live in this repo; data stays out of git | The data is 580 MB and licensed for attribution; the answer keys must not be published (see `data/README.md`) | team |
| 2026-11-06 | Licence for our own code: open, MIT proposed | the proving-ground code is MIT and the repo goes public Sunday | team, undecided |
| 2026-11-06 | The proving-ground zip is never attached to this repo or its releases | it holds truth/, holdout/ and row maps; releases go public with the repo | team |
| 2026-11-07 | Scenario: HEALTH-S1 (university research group, controlled research) is the scored story; HEALTH-S3 only as an optional second story if S1 scores by midday | One output cannot serve all three health scenarios, S1 covers all five demo items in one story and the organiser baseline leaves room (B2-k utility 0.40) | team |
| 2026-11-07 | Governance focus: who owns the release decision. The hospital's data steward signs the policy that sets the risk limits; `build` stays one command and refuses an unsigned or changed policy. Replaces the three-command design in `plans/2026-11-07-governance-focus.md` | The official named governance as the extra mile and could not be asked again, so Arda followed a Fable review's call | Arda |

To add a row: append one line to the table with the date (YYYY-MM-DD), the decision, the reason in one sentence, and who decided. Never edit old rows; add a new row that supersedes them.
