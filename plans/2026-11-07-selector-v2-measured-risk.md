# Selector v2: pick by measured risk, not by a hand-written order

Status: proposed. Author: Claude Fable 5.1, run by Arda, 2026-11-07. Comment inline as `> note (name):` or append a review section per `how-to-propose-and-review.md`. Nothing here is a team decision until a row lands in `../decisions.md`.

## In plain words

Today the tool decides how much to blur each column by walking down a list written by a person: hide it, show the decade, show the year, and so on, and it stops at the first step that still answers the researchers' questions. The order of that list is an opinion. For steps that are plain coarsenings of each other (a 20-year band of a 10-year band) the order is a fact; for the three time steps (month, ISO week, hour of day) and for the tuned numbers (8 towns, 20 years, 2 decimals) it is a guess nobody tested.

This plan removes the order. For every column the tool tries every blur option, keeps the ones that still answer the researchers' questions, measures for each how many people in the resulting table could be picked out by someone who knows every value in the table, and keeps the most useful option whose count stays under a stated safety line. The order is gone; a stated rule and a count on the data decide. Each decision carries its numbers so a judge can read why.

Verified today: re-running the current chooser reproduces the shipped `contracts/HEALTH-S1.json` byte for byte (70 seconds), so "the tool wrote the shipped contract" is true. This plan changes what the tool does when it writes one.

## How to read this

- Contract: the JSON file of per-column decisions the build applies (`contracts/<scenario>.json`). The build only runs the selector when no contract file exists.
- Candidate: one blur option for a column (`selector.candidates()`); the set is taken from the organisers' `PET_PLAYBOOK.md`. The set stays; its order stops meaning anything.
- Feasible: a candidate under which every required utility task of the scenario stays within TOL (0.05) of the reference release, measured with the organisers' `run_utility`. Unchanged from today.
- Knowable columns: every kept column of the main table whose values an attacker could plausibly hold, which here means every kept column except: dropped columns, keyed tokens, free text, and numerical measurements (vitals, minutes, amounts). Team call 2026-11-07: measurements are the secret, not the key.
- Risk of a candidate: on the release with that candidate applied and every other column at its current choice, the share of main-table rows whose combination of knowable values is shared by fewer than 5 rows. Attacker-agnostic: it uses no attacker file and no catalogue of quasi-identifiers.
- Safety line (RISK_LINE): the share of rows allowed above. Default 0.05. A stated policy number, set by the team, printed in every reason.

## What we build

1. `selector.py`: for each column of a released table, evaluate every candidate: utility scores (as today) and risk (new). Decision rule: among feasible candidates with risk below RISK_LINE, the one with the highest mean utility; if none is below the line, the feasible one with the lowest risk, and the reason says the line was not met; if none is feasible, today's fallback (best scores). `candidates()` keeps its lists as the menu; no code may depend on their order.
2. The post-repair pass (today: "one rung more private") becomes the same rule re-run on the repaired release: among candidates feasible on the repaired release and below the line, highest mean utility; at most 3 rounds, as today.
3. A `risk()` helper, in `selector.py` or `checks.py`, that takes the release frame, the contract, the labels, and returns the k<5 share over knowable columns plus the list of columns it used. Numerical measurements identified from the detector's subtype where it says so, else from a numeric dtype with many distinct values; the helper prints which columns it treated as knowable so the choice is auditable.
4. Reasons: "Candidates tried: drop (utility H-U2 1.00 ... ; risk 0.00); month (...; risk 0.31); ... Chosen: week, highest utility under the risk line 0.05." Evidence JSON gains `risk` per candidate and the knowable column list.
5. Tests in `tests/test_release_gate.py`: rewrite the one at line 144 ("most private candidate that keeps the task") to the new rule; add one that a numerical column is excluded from the knowable set; add one where two feasible candidates differ only in risk and the one under the line wins; keep line 192 (it uses `candidates()` as a name list only). All 48 existing tests must still pass.
6. `README.md` selector section: replace the ladder paragraph with the rule above, the knowable-column definition and the line.

Not in scope tonight: ENERGY-S3 regeneration (several minutes and GBs per run), a global optimiser across columns, changing TOL or k=5.

## Numbers we expect and where they come from

- Task 0 measures the baseline first: risk of today's shipped HEALTH-S1 release over knowable columns. Unknown tonight; the informed-attacker check with only four columns known already singles out 0.128 of visits (`results/health-s1-build/checks/informed_attacker.json`), so the all-columns figure will be higher. The team sets RISK_LINE after seeing it.
- Organisers' privacy score cannot fall: the new rule blurs the 8 catalogued quasi-identifiers at least as much as any feasible choice did before, and the attacker-file checks only gain from blur.
- Organisers' utility score stays within TOL of the reference by construction; it may land below today's 0.971 if the line forces a coarser pick.

## Build order

0. Baseline: script or test that computes risk over knowable columns on the shipped release and on the raw table; report both. 30 minutes.
1. `risk()` helper plus its tests. 45 minutes.
2. Decision rule in `select()` and the post-repair pass; reasons; evidence. 60 minutes.
3. README section. 15 minutes.
4. Regenerate `HEALTH-S1` to `contracts/generated/HEALTH-S1.v2.json`, diff against the shipped one, run `build --contract` on it, compare `scorecard.json` with `results/health-s1-build/scorecard.json`. Same for HEALTH-S3 and EDU-S2 as a generality check. 60 minutes.
5. Review by an agent that did not write the code, premortem first (how does it wrongly pass, wrongly block, misfire on another dataset), re-running every command above. 45 minutes.

## Ship rule (team, 2026-11-07, no time limit)

The v2 contract replaces the shipped one only if all four hold: the full gate passes; the organisers' privacy score is at least today's (0.953); the organisers' utility score is within 0.02 of today's (0.971); the reviewer verdict is GO, or RESHAPE with the fixes applied. Otherwise the shipped contract stays and v2 goes into the deck as the next version with its evidence table. Work continues until the four hold or Arda stops it.

## Demo script change

Slide: "the tool measures, a stated rule decides." Two numbers per release, both labelled: the organisers' privacy score, and our stricter count assuming the attacker knows every value in the table. The three time options are no longer a judgement call; the line and the knowable-column definition are, and they are printed.

## Limitations we will state

- Risk is measured one column at a time with the others held at their current choice (greedy). Two passes and the repair search cover most of it; it is not a global optimum.
- The safety line and TOL are policy numbers chosen by the team.
- Numerical measurements are excluded from the attacker's assumed knowledge by decision, not by measurement.
- The menu of candidates is the organisers' playbook; a transformation not in it cannot be chosen.

## Questions for the team

1. RISK_LINE after Task 0: keep 0.05, or set it relative to the baseline?
2. Should the stricter count also appear in `pets_submission/` reports, or only in the deck?

## Amendments after premortem and baseline (author, 2026-11-07, approved by Arda in chat)

These supersede the matching items above. The implementer follows this section where it conflicts with the text above.

- **Baseline measured** (`scripts/risk_baseline.py`, ed_visits, 46,398 rows): the shipped release keeps 10 of 29 columns; 5 are knowable under the first definition (date_of_birth band, municipality, arrival hour, triage, icd10_primary). k<5 share with all 5 known: 0.8803. On the 3 catalogued quasi-identifiers that survive: 0.0000. The 0.88 is driven by triage and icd10_primary, which are what the recipient needs. A 0.05 line on that count cannot be met without hiding the diagnosis.
- **Knowable columns, revised:** the columns the detector labels `quasi_identifier` (any subtype, on any dataset) plus kept `non_sensitive` columns with CATEGORY subtype and at most 20 distinct values. `sensitive_attribute` columns (diagnosis codes, triage, vitals, flags) are the target, never the key; keyed tokens, dropped columns and free text are out. No catalogue file and no attacker file is read.
- **Numerical measurements:** nothing to detect any more; sensitive_attribute is excluded as a role. The numeric fallback is removed. Quasi-identifier columns are never removed from the knowable set by any dtype test.
- **Risk of a candidate:** measured on the column's own table (not only the main table), before the k repair, with every column not yet judged set to `drop` (so unjudged columns do not inflate uniqueness). The main table for the k target is fixed from the reference release.
- **Decision rule, with tie-break:** among feasible candidates with risk below RISK_LINE (0.05, printed in every reason), the highest mean utility; ties within 1e-9 go to the lowest risk, then to the candidate name in alphabetical order. If none is below the line: the feasible one with the lowest risk, reason says "line not met". If none is feasible: today's fallback (best scores). No code path may use the position in `candidates()`.
- **Repair pass:** the same rule re-run on the repaired release, where feasible means "mean utility no worse than the current repaired scores" (today's criterion at selector.py:205), not "within TOL of the reference" (the premortem showed test :196-218 fails otherwise). At most 3 rounds. Reference release for unjudged columns stays the finest candidate (today's :112), since the reference exists to measure the most utility available, not risk.
- **Reported, not enforced:** the "attacker knows every kept value" count (all kept columns except tokens and free text) is computed once on the final repaired release of each released table and written to the contract under `fitness` with the scenario's `trust_level`. It decides nothing in selection; it goes on the slide as the fit-for-sharing statement (demo item 5).
- **Privacy claim dropped:** the sentence "organisers' privacy score cannot fall" is withdrawn. v2 keeps finer values than v1 wherever the line allows, so the organisers' k and linkage components can rise. The four-check ship rule is the only guard.
- **Post-repair risk:** the k repair targets the detected quasi-identifiers only; if post-repair risk on knowable columns is still above the line the reason says "line not met after repair". Never claim the line holds unless measured.
- **Lines still tied to order to change:** selector.py :112 (reference = `ladder[-1]`: keep, but comment that it is the finest candidate, not an order), :148 (single-candidate shortcut: fine, it is about list length), :171 and :219 reason text ("most private first", "is more private": rewrite), :196-211 (walk by index: replace with the rule). Test :193 asserts order on `candidates()` names: keep the menu order stable for that test, but no selector code may read it.
- **Cost:** a full menu sweep on time columns (6 candidates) times repair rounds multiplies today's 70 s run; expect several minutes per selection. Task 4 budgets 10 minutes per scenario.

## Review: Opus 5.5 premortem, run by Arda's session, 2026-11-07

Read: this plan, `selector.py`, `checks.py` 1-70, `protect.py` signatures, `detect.py` subtype vocabulary, `tests/test_release_gate.py` 100-220, `EVALUATION.md`, `THREAT_MODEL.md`. Facts checked against code by the reviewer itself. Nothing here is a team decision.

**Verdict:** RESHAPE. The rule is sound once the knowable set excludes sensitive attributes and the tie-break is stated; as first written the line was unreachable and the privacy claim false.

Findings (each folded into the amendments above): privacy claim false (v2 ends finer or equal to v1); risk on unjudged columns measured at the reference inflates uniqueness; the line unreachable with sensitive columns in the set; risk measured on the main table only lets other tables' candidates tie; subtype vocabulary cannot find vitals (MEASUREMENT, FINANCIAL_DATA, but integer vitals come back OTHER) and a dtype fallback would wrongly drop AGE, GPS, POSTCODE from the set; no tie-break stated; the repair-pass criterion would fail test :196-218; the repair never targets the knowable set; ten code lines still read ladder order; cost multiplies.

Not checked: HEALTH-S3 and EDU-S2 columns; `pio.load_tables` dtypes; the catalogue's QI list against the detector's; `repair.apply` internals.

## Corrections (author, 2026-11-07, after a fact check by the "Key decisions documentation" session)

- **Ship rule numbers were stale.** The shipped scorecard (`results/health-s1-build/scorecard.json`, summary block) reads privacy 1.0, utility 0.971, composite 0.9866. The 0.953 / 0.993 pair in the ship rule above came from an earlier release and is withdrawn. The rule now reads: organisers' privacy score at least 1.0 (the shipped value) and utility within 0.02 of 0.971, pending Arda's confirmation of the privacy bar.
- **0.8803 is not the `fitness` count.** It is the five-column baseline (knowable set under the first definition, measurements excluded). `fitness` counts every kept column except tokens and free text, so on the shipped release it includes temp_c and los_minutes and will be at least 0.8803. The implementer measures it; nobody quotes 0.8803 as fitness.
- **Scope of "sensitive is never the key":** it applies to the selector's risk measure only. The informed-attacker check (`checks.informed_attacker`, which assumes the diagnosis group is known) and the informed contract stay as they are.
- **Tie-break (a).** The order is "lower risk, then fewer distinct values in the protected column, then candidate name", as implemented in `selector.py` `_decide`. The amendment's "risk, then name" is superseded.
- **Triage (b).** The detector labels `ed_visits.triage` non_sensitive CATEGORY, not sensitive_attribute, so it is knowable. Post-repair risk on ed_visits is 0.1547 and the line is not met after repair. No slide may say the line holds on HEALTH-S1.
- **Limitation (c).** A non_sensitive column with more than 20 distinct values, or of a subtype other than CATEGORY, is not in the knowable set, so a high-cardinality identifying category would pass unmeasured.
- **Repair-pass feasibility (d).** The repair pass judges feasibility on the mean task score only, as the v1 code did, so one task may fall more than TOL below the reference.
- **Open question for the team (e).** EDU-S2 now keeps `students.special_support` (detector: non_sensitive CATEGORY; semantically sensitive) on a 0.0017 utility gain (EDU-U2 1.0 vs 0.9983) with students risk 0.0124. Decide on the label or a minimum utility gain before any EDU-S2 release.

## Review: Opus 5.5 (code-implementer, review mode), run by Arda's session, 2026-11-07

Read: this plan including Amendments and Corrections, the diff of selector.py, tests/test_release_gate.py and README.md, results/selection/v2-comparison.md. Re-ran pytest (70 passed), a scratch script showing the new tie test fails under the old rule, an em-dash grep (none), and a column-by-column comparison of the v2 and shipped HEALTH-S1 contracts (38 of 38 equal on pet and params; table actions, k_target and k_columns equal). Nothing here is a team decision.

**Verdict:** RESHAPE. Logic matches the amended plan and HEALTH-S1 is unchanged, but the plan text (tie-break, triage), the README repair-risk wording and the no-repair reason text need fixing before GO.

**Tie-break order.** Code and README say risk, then fewer distinct values, then name; the amendment said risk, then name. The code is right (under the amendment "8 most common" would beat "drop"). Fix: amend the plan.

**Repair-pass wording.** Risk is measured before the repair and utility after it; the README read as both after, and said "every kept QI" although dropped ones are judged again. Fix: reword.

**No-repair reason.** The reason says "After the k repair" even when no k target exists (EDU-S2). Fix: say "on the final release".

**Knowable set edge.** A plain category with more than 20 values, or another subtype, leaves the knowable set; follows the plan, but a high-cardinality identifying category would pass unmeasured. Fix: state as a limitation.

**Triage label.** The detector labels triage non_sensitive CATEGORY, so it is knowable; post-repair risk on ed_visits is 0.1547 and the line is not met after repair. Fix: correct the plan; no slide may claim the line holds.

EDU-S2: the two moves (school_code, special_support from drop to keep) are the rule working as intended, not a defect; the fault is the label of special_support, which the team should decide. Also noted: repair-pass feasibility checks the mean only (as v1 did); a test comment says the name decides when distinct values decide first; the README evidence pointer names only the v1 file.

Not checked: the HEALTH-S1 build or scorecard (not re-run by the reviewer); HEALTH-S3 select; repair.apply internals; detector labelling beyond the named columns.

Fixes applied by a separate Sonnet worker, 2026-11-07: the review findings above, wording and plan text only (one reason-text branch in selector.py).
