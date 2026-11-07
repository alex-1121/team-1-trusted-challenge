# Key decisions

Every choice that shaped this project, from the Friday challenge pick (6 November 2026) to the state of main on 7 November 2026, split by who made it. Section 1 holds the decisions teammates made. Section 2 holds the decisions an AI model made while building, reviewing or proposing, with the model and the teammate who ran it named on each row. Section 3 lists what is still open.

How to read this:

- Only `decisions.md` makes something a team decision. A row in section 2 is a design choice that is built into the code or a proposal in a plan. The team can overrule any of them.
- Status words: DECIDED (a row in `decisions.md`), ADOPTED (a rule or text a teammate merged into main, with no `decisions.md` row), BUILT (in the code on main, open to the team), PROPOSED (in a plan or review only, never adopted), OPEN (named as undecided).
- Terms: a PET is a privacy-enhancing technique (a way to protect a column, such as dropping it or coarsening it). k-anonymity means every row shares its identifying values with at least k other rows. l-diversity means each such group holds at least l distinct sensitive values, here diagnoses. A contract is the JSON file that says which PET applies to which column. The release gate is the step that refuses to write the submission folder when an attack or a utility floor fails. pets-eval is the organisers' scoring toolkit. A composite score is its weighted mean of privacy and utility.
- Numbers are self-assessment from committed scorecards, never the judges' grade.
- Sources are paths in this repo unless marked "cockpit" (Arda's private repo, `sinceai-hackathon-2026/` and `decisions/log.md`).

## 1. Teammate key decisions

| Date | Decision | Why | Who | Status | Source |
|---|---|---|---|---|---|
| 2026-11-06 | TrustED PETs Transformer is our challenge | Team pick at the Friday selection. The research Arda's agents ran had ranked TrustED last on win odds; the team overruled it | team | DECIDED | `decisions.md`; cockpit `research/01-review.md` |
| 2026-11-06 | Code and context live in a separate team repo (`alex-1121/team-1-trusted`, under Alex's GitHub account), the cockpit keeps Arda's private context | The submission needs a public repo every teammate commits to, and the cockpit is private | Arda's decision; team row | DECIDED | `decisions.md`; cockpit `sinceai-hackathon-2026/build/README.md` |
| 2026-11-06 | The proving-ground data stays out of git everywhere; the zip is never attached to the repo or a release; `truth/`, `holdout/` and `rowmap_*.csv` never land in git or the source zip | 580 MB, licensed for attribution, and the answer keys must not be published (row maps are an organiser rule, truth and holdout are the team's own caution) | team | DECIDED | `decisions.md`; `AGENTS.md`; `data/README.md` |
| 2026-11-06 | Licence for our own code: MIT | The proving-ground code is MIT and the repo goes public Sunday | team | OPEN (proposed, undecided) | `decisions.md` |
| 2026-11-06 | Working method: one plan per file, reviews append below the author's text, facts and judgement checked by different people, a pick becomes real only as a row in `decisions.md` | So a model's verdict can never pass for a team decision | Arda wrote it (PR #9), team adopted it by merge | ADOPTED | `plans/how-to-propose-and-review.md`, `plans/README.md` |
| 2026-11-06 | Claim rules: never write "anonymised", "GDPR compliant" or "differentially private" without the method and its parameters; every number comes from a committed scorecard JSON; no fabricated numbers; no em-dash in anything shipped | Honesty with judges and the data licence | Arda wrote it in the context pack (PR #1), team adopted it by merge | ADOPTED | `AGENTS.md` |
| 2026-11-06 | Scope freeze Saturday 18:00, video recorded then, as the team's own buffer before the Sunday 10:00 deadline | The vote card is built from the submission form | team plan (Arda's context pack) | ADOPTED | `team/plan.md`; `plans/2026-11-07-health-s1-spec.md` |
| 2026-11-07 | HEALTH-S1 (university research group, controlled research) is the one scored scenario; HEALTH-S3 only as an optional second story if S1 scores by midday; HEALTH-S2 rejected as the main story | One output cannot serve all three health scenarios, S1 covers all five demo items in one story, and the organiser baseline leaves room (B2-k utility 0.40) | team, Arda in chat; row merged by Arda (PR #10) | DECIDED | `decisions.md`; cockpit `decisions/log.md` 2026-11-07 |
| 2026-11-07 | Hands-off overnight build, run locally by one master session, tickets A to H, each reviewed by a worker that did not write it, no budget cap, merged to main (PRs #20 to #30, #32) | Four people could not build it by hand before Sunday | Arda ordered it | DECIDED | cockpit `decisions/log.md` 2026-11-07; PR list of this repo |
| 2026-11-07 | Devin agents and Anthropic cloud sessions dropped; the private fork made for Devin archived | The data sits only on Arda's laptop and the repo belongs to Alex, so neither could reach the work | Arda | DECIDED | cockpit `decisions/log.md` 2026-11-07 |
| 2026-11-07 | The release-gate work (built by Opus 5.5, see section 2) goes into main as the default build | The red team had broken the ticket-H release at commit 7cf541b (order attack rebuilt dropped dates on every row) | Tadek fast-forwarded it into main | ADOPTED (by merge) | `plans/2026-11-07-release-gate.md` status line; commits f8ae369 to 2c228b1 |
| 2026-11-07 | Git rules: no force-push to main, no `reset --hard`, `pull --rebase` before push, an agent commits or pushes only when the teammate running it asks | A push must never overwrite a teammate's work | Alex (PR #35) | ADOPTED | `AGENTS.md` Git section |
| 2026-11-07 | `CLAUDE.md` only imports `AGENTS.md`; the README keeps a project index that every change updates | One rule file for every agent, one map for every reader | Alex (PRs #33, #34, #36) | ADOPTED | `CLAUDE.md`, `README.md` |
| 2026-11-07 | The cross-release linkage limitation is stated in the docs (two releases with different keys cannot be joined, and that is a limit as well as a feature) | Honest limits | Alex (PR #39) | ADOPTED | commit 42cb1c3 |
| 2026-11-07 | A full repository audit by Codex (GPT-6 Astra) is committed as findings for team review, not as decisions | Second-opinion check before submission | committed by NKizo (b9311b4); the file names no runner | findings only | `plans/review_by_astra.md` |
| 2026-11-07 | The organisers' reply of 7 November (one scenario is enough, explain the trade-offs) is recorded verbatim as context | It settles the "one scenario or three" question | Arda (PR #38) | context | `context/` |

## 2. AI key decisions

Each row names the model and the teammate who ran it. "Fable" is Claude Fable 5.1, run by Arda unless stated. "Opus" is Claude Opus 5.5, run by Tadek for the release gate and used as the blind checker in Arda's reviews.

### 2a. Proposals and reviews (never adopted as written)

| Date | Decision | Why | Model, run by | Status | Source |
|---|---|---|---|---|---|
| 2026-11-06 | Research ranking before the pick (the later, reviewed version): Traficom first if a propagation-model defender exists, otherwise Fonecta; Apetit third; TrustED last | Win-odds scoring across the five challenges | Fable and research workers, run by Arda | PROPOSED, overruled by the team's TrustED pick | cockpit `research/01-review.md` (the earlier `00-scoring-and-recommendation.md` had Apetit second) |
| 2026-11-06 | Review of Tadek's DP query vault plan: verdict RESHAPE; fixed question templates with a validator, the LLM behind a switch, offline demo, wallet cut to one slide; release synthetic row-level `ed_visits` next to the DP answers because H-U1 and H-U8 need rows | Agent and wallet earn no points; overall utility about 0.23 without row-level data (the candidates file says about 0.33) | Fable, run by Arda | PROPOSED, not adopted (the vault was not built) | `plans/2026-11-06-query-vault.md` review section |
| 2026-11-06 | Seven build-idea candidates (A to G, G being Tadek's vault); recommendation: candidate A on HEALTH-S1 with HEALTH-S3 shown as a second scenario in the demo, the free-text module as the cut line | One story covers all four verbs of the brief | Fable (Arda's agent) | PROPOSED, the team's S1 pick agrees with it | `plans/2026-11-06-build-idea-candidates.md` |
| 2026-11-07 | After the S1 pick: the arrival-time trap named (H-U8 needs a clock time while `arrival_ts` is a scored quasi-identifier; coarser kills H-U8, finer leaves rows unique); run one scorecard on a hand-made protected copy before writing any program | Hour-only escape was unverified | Fable with a blind Opus checker, run by Arda | PROPOSED, then done as the gate run (PR #11) | `plans/2026-11-06-build-idea-candidates.md` review section |
| 2026-11-07 | Repository audit: about 75 percent fit to the challenge, 70 percent to the current objectives; P1 and P2 fixes listed | Pre-submission check | Codex GPT-6 Astra, run by NKizo | findings, OPEN | `plans/review_by_astra.md` |
| 2026-11-07 | Handover of the row maps to the organisers: route A a private upload the organisers name, route B an AES-256 archive with the password sent on another channel | Row maps must reach the organisers without going public | Fable (deliverables ticket F) | PROPOSED, team picks after the Discord answer | `docs/pets-submission-handover.md` |

### 2b. The spec (Fable, run by Arda, unattended, 2026-11-07, "every choice open to the team")

| Decision | Why | Status | Source |
|---|---|---|---|
| One Python package, plain pandas, three commands: detect, protect, score | No heavy dependency, four people can read it | BUILT | `plans/2026-11-07-health-s1-spec.md`; `src/pets_transformer/` |
| Out of scope: natural-language interpreter, an LLM choosing PETs, a learned selector, a per-PET grid, a notes redactor, differential privacy, HEALTH-S3 as a built second story | No S1 task needs them; DP is not needed for S1 | BUILT as scope (the release gate later scored HEALTH-S3 anyway as a generality check, see 2d) | spec section "out of scope" |
| `arrival_ts` becomes hour of day only, the date is dropped | Gate run: month or week scores H-U8 at 0.0, hour at 1.0; costs seasonality | BUILT | spec; `README.md` |
| IDs become keyed HMAC-SHA256 tokens, plain hashes forbidden, a fresh random key every build, the key never handed over and never inside the release folder | A plain hash is reversible from the public ID format; two releases stay unjoinable | BUILT | spec; `docs/guarantee-and-residual-risk.md` |
| Date of birth becomes a 10-year age band (band width a sweep parameter) | k on the age band instead of a birth date | BUILT | spec; `README.md` |
| Municipality: the eight most common kept exact, the rest "other" | H-U4 needs the eight largest municipalities | BUILT | spec; `README.md` |
| Drop `discharge_ts`, `ambulance_unit`, postcode, date of birth, `chief_complaint`, lab `sampled_ts`; withhold `clinical_notes` and `published_weekly_stats` | No S1 task reads them; a withheld table leaks nothing | BUILT (the selector later also dropped sex, most vitals, secondary diagnosis, disposition, arrival mode) | spec; `results/selection/HEALTH-S1.json` |
| Detector works on column values only, never names; tuned on a subset, scored held-out; target macro-F1 above the organiser baseline B1 0.65 | "Catalog on catalog" is not a result | BUILT (held-out macro-F1 on health 0.8086 before the second look, 0.8202 after; eight rules were added after reading errors, so the score is flagged tuned, not clean) | spec; `results/detect/RESULTS.md`; `README.md` |
| Sweep only the age band width and the k target, pick the best composite above a task floor | Show the parameters instead of guessing | BUILT differently: a 9-cell sweep over band width (5, 10, 20 years) and hour block (1, 2, 3 hours), task floor 0.90, no k-target axis | spec; `src/pets_transformer/sweep.py` |

### 2c. The overnight build, tickets A to H (Fable master session with Sonnet and Opus workers, run by Arda, 2026-11-07)

| Decision | Why | Status | Source |
|---|---|---|---|
| The HMAC key is generated per run from `os.urandom` and written beside the release folder, which is git-ignored | A key inside the release would travel with it | BUILT | commit d2c4578; `README.md` |
| A missing HETU (Finnish personal identity code) stays missing instead of getting a token | A token for nothing invents a person | BUILT | commit d2c4578 |
| The detector reads the first 5000 rows, and a non-sensitive label gets a second look on 5000 rows from the whole file that can only move it to a more protective label | Time-sorted tables show only the early weeks | BUILT | `src/pets_transformer/detect.py` |
| The build checks the unseen folder and the baseline before any work; tests cover every taxonomy role | Fail early | BUILT | commit 5d24a36 |
| `arrival_mode` dropped from `ed_visits` | l-diversity fix: with it kept, groups shared a single diagnosis; composite went from 0.9346 to 0.9709 | BUILT (PR #32) | commit eaa9e93 |
| Three checks the scorecard does not run: l-diversity, an informed attacker, joined-table k | The organiser scorer sees none of them; the documents state all three | BUILT (PR #32) | commit a7c9b76; `README.md` |
| The 0.99 from the first gate run is never quoted | It was inflated by an age band in a column the scorer could not see | BUILT into every text | cockpit `decisions/log.md` 2026-11-07 |
| Quoted numbers are the H-release self-assessment (privacy 0.953, utility 0.993, composite 0.971 against baseline B0 0.275) with the limits beside them: 7.8 percent of rows under k 5, 11 percent of look-alike groups single-diagnosis, an informed attacker singles out 12.8 percent | Honest limits beside every number | BUILT into README, guarantee doc, video script, deck outline (superseded on the gated release, see 2d) | `README.md`; `docs/guarantee-and-residual-risk.md` |
| Tech chips for the vote card: Python, pandas, HMAC-SHA256, k-anonymity, pets-eval | Five chips show on the card | BUILT into the filled checklist | `team/submission-checklist.md`; `docs/deck-outline.md` |
| Video script 260 words, deck outline 10 slides (the outline now holds 12), README demo in the five demo items | Submission format | BUILT | `docs/video-script.md`; `docs/deck-outline.md` |
| The two label CSVs (`unseen_field_labels.csv`, `health_field_labels.csv`) are the only files committed under `pets_submission/` | The hidden detection check needs them; everything else there is never committed | BUILT | `docs/pets-submission-handover.md`; `.gitignore` |

### 2d. The release gate (Opus 5.5, run by Tadek, 2026-11-07, merged into main by Tadek)

| Decision | Why | Status | Source |
|---|---|---|---|
| Pipeline is detect, select, protect, repair, score, attack, then refuse or release | Turns a 0.9709 release that leaked into a gated one | BUILT | `plans/2026-11-07-release-gate.md` |
| Selector: per column, a ladder of PETs from most private down; keep the first rung where every required task stays within 0.05 of the exact-data release; a second pass on the repaired release moves a kept column one rung more private if the mean task score holds | Objective 2 of the brief done by the tool, not by hand; nothing moved on HEALTH-S1 | BUILT | `src/pets_transformer/selector.py`; `README.md` |
| k target 5 and l-diversity minimum 2 distinct primary diagnoses on every row of `ed_visits`, measured over age band, municipality and arrival hour | The scorer measures k; l stops a group that shares one diagnosis from telling it | BUILT | `contracts/HEALTH-S1.json`; `docs/guarantee-and-residual-risk.md` |
| The lab-presence flag is part of the k columns: visits with lab results must sit in a group of at least five such visits | Researchers hold both tables, so the release shows which visits have labs; composite 0.9866 with the flag against 0.992 without, and 5.5 percent of visits in smaller groups without it | BUILT, listed as open for the team | `plans/2026-11-07-release-gate.md` "Open for the team" |
| Repair only the at-risk rows (k under 5 or l under 2), stepwise: 20-year age band, then a 3-hour arrival block written as a range "HH:00 to HH:59", then municipality "other", then suppress; a row drop is the last resort; the step order was chosen by scoring all six orders | A block start written as "14:00" reads as an exact hour; result 3746 rows repaired, 59 suppressed, none dropped, minimum k 5 | BUILT | `contracts/HEALTH-S1.json`; `results/health-s1-build/repair_report.json` |
| Every released table is shuffled with a cryptographic random permutation and the row map follows it | The order attack rebuilt the dropped dates from file order on 100 percent of rows | BUILT | `plans/2026-11-07-release-gate.md`; `results/redteam/` |
| No patient pseudonym is released, although the organisers suggest one | 29.4 percent of patients were unique by fingerprint; no HEALTH-S1 task needs it, H-U6 uses `readmit_30d` | BUILT, listed as open for the team | `plans/2026-11-07-release-gate.md`; `results/health-s1-pseudonym-build/` |
| The default contract is the selected one (known recipient under agreement); `HEALTH-S1-informed.json` closes the informed-attacker gap (composite 0.9647, H-U4 0.8334, H-U8 0.8485) for a less trusted recipient | The informed attacker still singles out 9.7 percent of visits on the default, 92.9 percent of them correctly | BUILT, listed as open for the team | `plans/2026-11-07-release-gate.md`; `README.md` |
| Gate thresholds: order attack 0.05, news linkage 0.0, person fingerprint 0.05, band-aware scorer linkage 0.01, plain hash 0.0, utility floor 0.5 per required task; a fail blocks `pets_submission/` | "Our choice", stated as such. Astra's audit notes the 0.5 floor is weaker than the selector's 0.05 tolerance and the repair search's 0.85 floor | BUILT, listed as open for the team | `src/pets_transformer/redteam.py`; `src/pets_transformer/build.py`; `plans/review_by_astra.md` |
| The selector's HEALTH-S1 contract stays the default; the hand-written contract is kept only for comparison | Hand-written scores 0.9877 against 0.9866, but puts 12.1 percent of lab visits in groups under 5 | BUILT | `plans/2026-11-07-release-gate.md` |
| Age is computed against a fixed reference date, 2025-12-31 (the evaluator's default), not the visit date | 2,492 of 46,398 rows land in a different band than age at visit; stated as a limit | BUILT (found by Astra's audit) | `plans/review_by_astra.md` |
| The fingerprint attack counts only per-person facts, never per-row timestamps | Avoids false positives | BUILT | release-gate plan, change 17 |
| The organisers' linkage attacker is rerun band-aware | It misreads "30-39" and "HH:00" as exact values | BUILT | `plans/2026-11-07-release-gate.md`; `docs/guarantee-and-residual-risk.md` |
| PUB-S3 is refused: the reviewed contract uses month, a 3-digit postcode, a 1 km grid and a duration instead of two timestamps, with the organisers' k key plus the grid; PUB-U1 still scores 0.3888 and PUB-U3 0.2987, under the 0.5 floor | Area counts and a hotspot map cannot both survive k at least 5 at row level | BUILT (the gate refuses it) | `contracts/PUB-S3.json`; release-gate plan |
| HEALTH-S3, EDU-S2 and ENERGY-S3 are also built with no hand-written rules (1.0, 0.9983, 1.0) as a generality check; the time ladder gained date and hour rungs | Shows the selector is not tuned to one scenario (conflicts with the spec's "no second story", kept as a check, not a story) | BUILT | `README.md`; release-gate plan |
| 2026-11-07, Opus 5.5, run by Arda: the gate became one function, `evaluate` in `redteam.py`, that also refuses on scorer min k under the target, joined min k on the k columns under the target, l under the target, a needed check that did not run, an attack that should have run but could not (each attack now reports pass, fail or not_applicable with a reason), a required task from the scenario definition missing or under 0.5, any identifier scan finding or a scan that did not run, a direct-identifier or free-text leakage risk above 0, and a CSV the contract does not name; only the contract's files are copied, and a withdrawn table loses its old files on rebuild. Thresholds unchanged | The no-flag build passed the old gate with a joined min k of 1, and Astra's stray-file probe passed it with an email in an extra CSV; the old gate read none of these results | BUILT | `src/pets_transformer/redteam.py`; `tests/test_gate.py`; `plans/review_by_astra.md` P1-1 and P1-2 |

## 3. Open, not decided

- Code licence (MIT proposed).
- Lab-presence flag in the k target, the informed-attacker contract as default or not, and the gate thresholds (all built by Opus, all marked open for the team).
- Row-map handover route (A or B), after the organisers answer on Discord.
- Astra's P1 and P2 findings.
- Sunday before 10:00 Turku time: record and upload the video, fill the submission form, fresh-clone install test, make the repo public.

To add a row: append to the right section with the date, the decision with its exact value, the reason in one clause, who (a teammate by name, or the model and who ran it), the status word, and the source. Never edit an old row; add a new one that supersedes it. A team decision also needs its row in `decisions.md`.
