# What is expected from us

Plain words for a team that has the data but not the picture. Everything here comes from the organiser files in this folder and the team plan; each section ends with a "Source:" line. Read this before `challenge-digest.md` if you want the why before the what.

## In one sentence

Build one working tool that looks at a sensitive dataset, works out which columns and text passages are dangerous, picks a protection technique for each one given who will receive the data, produces the protected files, and then proves with numbers that the protected data is both safer and still useful for one stated purpose.

Source: `brief.md` sections 02-03, `brief-onepager.md` (Objective).

## The deliverable is a tool, not a report

The organisers ask for "one working prototype". Our reading: a slide deck that explains PETs, or a notebook with manual edits, is not what they mean. The prototype has four verbs:

| Verb | What it means in practice | How it is checked |
|---|---|---|
| Detect | Classify every column (direct identifier, quasi-identifier, sensitive attribute, technical identifier, free text, record key, non-sensitive) and find personal data inside free text | `pets-eval detect` against `metadata/field_catalog.csv`; `pets-eval text` against the gold PII spans |
| Select | Choose a PET per data type, and tie the choice to the sharing scenario (who gets the data, why) | Judges read the justification; `docs/PET_PLAYBOOK.md` is the field guide |
| Transform | Write the protected tables or a protected view | `pets-eval check` scans the output for leftover identifiers |
| Demonstrate | Show risk removed and utility kept, before vs after, for one scenario | `pets-eval scorecard` writes the JSON and HTML we quote from |

The baselines "cheat" on the first verb: they read the field catalog instead of detecting. The organisers say it in plain words: "Your tool should detect fields itself." Detection is therefore part of the job, not an optional extra.

Source: `brief.md` section 01, `brief-onepager.md` (Objective), `proving-ground/START_HERE.md` ("The 30-second version"), `proving-ground/baselines/README.md`.

## The five things the final demo must show

All five, no exceptions. Each one maps to a file we can produce.

| # | Demo item | Our evidence |
|---|---|---|
| 1 | The data types identified in the original dataset | The detector's label file, plus its `pets-eval detect` score |
| 2 | The PETs selected for each data type | A table: column, role, PET, parameters, reason tied to the scenario |
| 3 | The transformed dataset or protected view | The output folder, committed or shown live |
| 4 | Utility before and after the transformation | The scorecard: utility tasks the scenario needs, original vs protected |
| 5 | The sharing scenario the protected data is suitable for | One scenario from `docs/SCENARIOS.md`, plus the residual risks the scorecard reports |

Source: `brief-onepager.md` (Final demonstration), `proving-ground/START_HERE.md` ("What the final demo must show").

## How we are judged

- Four Since AI criteria, no weights: technical implementation (correct, reliable PET choices), innovation (an intelligent, explainable approach), impact (evidence of reduced disclosure risk with preserved utility), presentation (clear scenario, before/after comparison, honest limitations).
- TrustED's own people evaluate remotely on Sunday morning. They are not on site. They see what we submit in sinceai.app, so the video, description and deck carry the whole story.
- The builder vote runs in parallel and sees even less: tagline, the description, the video, the deck and five tech chips. The repo is not on the vote card.
- Prizes for this challenge: EUR 2,000 / 750 / 250.

Source: `brief.md` sections 06-08, `../team/plan.md` (Judging, Schedule), `../team/submission-checklist.md`.

## What "good" means to the people who wrote the challenge

The organiser docs repeat the same points in several places. Treat them as the marking scheme behind the four criteria.

1. Hiding values is not enough. The best solutions keep "the patterns, distributions, trends, relationships or indicators needed for the intended use case".
2. Say what the guarantee is. "Anonymised" and "differentially private" are claims that need a method and parameters. For DP that means the mechanism, epsilon (and delta if any), the contribution bound and the unit of privacy (visit or person).
3. Report residual risk honestly: which attacks still work, at what rate. Honest limitations are named in the presentation criterion itself.
4. Justify every technique against the scenario. The same column can need tokenisation in one scenario and deletion in another.
5. Use AI only where it adds value, and justify every technique.
6. Protection is only meaningful against a stated attacker. The package ships attacker files so a privacy claim can be tested, not asserted.

Source: `brief.md` section 04, `brief-onepager.md` (Final demonstration), `proving-ground/START_HERE.md` ("Rules of the road"), `proving-ground/docs/PET_PLAYBOOK.md` ("Differential privacy in one paragraph", "Evidence the jury will look for"), `proving-ground/docs/THREAT_MODEL.md`.

## Where the points are

The benchmark page tells us where the simple baselines fail. Those gaps are where a weekend team can beat them.

| Gap | Evidence | What it means for us |
|---|---|---|
| Detecting sensitive attributes | The rule-based detector B1 has recall 0.10 on sensitive attributes (macro-F1 0.65 overall) | A detector that finds diagnoses, union fees, support levels and similar columns is a visible win |
| Free text | Regex redaction misses names, spoken numbers and spelled-out emails; "free-text leakage is where most teams can win" | A hybrid rule plus model redactor with typed placeholders, checked with `pets-eval text` |
| Uniqueness after generalising | B2 generalises columns but leaves most rows unique; B2-k fixes that at a large utility cost in some scenarios (HEALTH-S2 drops to 0.00) | Coarsen quasi-identifiers together and check k, but choose per scenario what to sacrifice |
| Joins | Keyed pseudonyms keep joins; random tokens or dropped keys break the cyber and revisit analyses | Use HMAC with a secret key where records must stay linkable |
| Receipts and timestamps | Under B0 a shared receipt (date, time, amount) still singles out 79 % of targets in card transactions | Exact timestamps and amounts are quasi-identifiers; round or shift them |
| DP parameters | Utility depends on epsilon and contribution bounding; the B3 table gives the curve | State both, and bound contributions per person first |

Source: `proving-ground/docs/BENCHMARK.md` (B1 table, "What the baselines teach"), `proving-ground/docs/PET_PLAYBOOK.md`.

## What we hand in on Sunday

- One submission in sinceai.app before 10:00 Turku time.
- A demo video on YouTube (public or unlisted), ideally under 2 minutes, English narration recommended.
- A clear description, a deck, five tech chips, and the source zip (up to 100 MB, no data files).
- The five demo items above, visible in the video and the deck.
- Optional: a `pets_submission/` folder so the organisers can run the hidden checks (stronger attackers, private `unseen` labels, hidden `customer_service` eval spans). This folder needs row maps, which must never be published, so how to hand it over is still an open question for the TrustED Discord channel.

Source: `brief.md` section 07, `../team/submission-checklist.md`, `proving-ground/docs/EVALUATION.md` ("Optional organiser checks").

## What is not expected

- No real data, no TrustED account, no API, no production data.
- Not all ten datasets. One dataset and one scenario, done well, satisfies the brief. The seven suggested paths are suggestions; teams may combine them.
- No new rubric to satisfy; the four Since AI criteria are the whole list.
- Not a TrustED deliverable. The proving ground was built by Since AI ry, inspired by TrustED's brief. Our reading: we are not expected to match TrustED's internal architecture, only its intent: protect data, keep its value.

Source: `brief.md` sections 05-06, `proving-ground/START_HERE.md` ("Choose your path"), `proving-ground/docs/LIMITATIONS.md`.

## Open questions

- How to hand `pets_submission/` to the organisers without publishing row maps (ask on the TrustED Discord channel).
- What the full challenge text in sinceai.app adds beyond the zip (compare after Friday 19:30).
- Which dataset and scenario we pick (the Friday-night decision; see `../team/plan.md`).
