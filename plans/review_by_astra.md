# Full repository audit, 7 November 2026

Status - audit findings for team review. Prepared by Codex using GPT-6 Astra, with separate implementation, evaluation and objectives reviews. The numerical claims and objective coverage were checked by the objectives reviewer, and the implementation findings by the privacy reviewer. Their precision corrections are incorporated here. These findings and completeness estimates are the auditors' judgment. Team decisions remain in `decisions.md`.

The project has a substantial, working HEALTH-S1 prototype. Its selected research analyses remain useful, and the main before/after result reproduces. The largest gaps are release enforcement and the breadth of the privacy evidence. A successful scorecard can coexist with identifier leakage, untested scenario threats and optimistic model validation.

The audit estimates **75% completion against the original challenge** and **70% against our current project objectives**. These are judgment-based estimates with roughly ten percentage points of uncertainty. They measure delivered and verified work. They are separate from the organisers' scores and from a probability of winning.

**Scope and evidence**

The source revision was `1b9b8dec6321627a259451094c14aa56033c1a1f`. Review covered the current implementation, tests, contracts, existing results, raw baselines, challenge materials, plans, decisions and presentation documents. The local organiser toolkit was inspected where the project depends on its scoring behavior.

All **87 tests passed** in 25.28 seconds. Eight builds across seven distinct scenarios ran in an isolated archive of that revision. They used the installed environment and the private proving-ground data. This verifies the current installation and source archive. A new dependency installation on a clean machine remains unverified. Other scenarios received static review rather than fresh execution.

Fresh JSON evidence is in [the audit evidence directory](../results/audit-2026-11-07/manifest.json). Original baseline files were already committed and were compared without regeneration. The evidence excludes data tables, keys, truth, holdout data and row maps. Raw runtime outputs remain privately under `/tmp/trusted-audit-20261107/`.

**Fresh scenario results**

Scores are the organisers' self-assessment on a zero-to-one scale. Utility is a mean of specific task scores with different normalisations. It does not measure the fraction of every possible analysis preserved. In these runs, privacy 1.000 means all evaluated risk components contributing to that score were zero.

| Build | Raw privacy | Raw utility | Raw composite | Protected privacy | Protected utility | Protected composite | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| HEALTH-S1 | 0.1716 | 1.0000 | 0.2752 | 1.0000 | 0.9710 | 0.9866 | Pass |
| HEALTH-S3 | 0.1728 | 1.0000 | 0.2769 | 1.0000 | 1.0000 | 1.0000 | Pass |
| EDU-S2 | 0.2190 | 1.0000 | 0.3395 | 1.0000 | 0.9963 | 0.9983 | Pass |
| ENERGY-S3 | 0.2275 | 1.0000 | 0.3506 | 1.0000 | 0.9973 | 0.9988 | Pass |
| PUB-S3, reviewed | 0.0833 | 1.0000 | 0.1429 | 1.0000 | 0.5547 | 0.7327 | Refused |
| PUB-S3, automatic | 0.0833 | 1.0000 | 0.1429 | 1.0000 | 0.2131 | 0.3734 | Refused |
| HEALTH-S2 | 0.1728 | 1.0000 | 0.2769 | 1.0000 | 0.3333 | 0.5238 | Refused |
| CS-S1 | 0.0622 | 1.0000 | 0.1084 | 1.0000 | 0.5000 | 0.6875 | Refused |

HEALTH-S1 and reviewed PUB-S3 used their reviewed contracts. HEALTH-S3, EDU-S2, HEALTH-S2 and CS-S1 reran automatic selection. ENERGY-S3 and automatic PUB-S3 replayed committed generated contracts. All cases ran protection, scoring and the release gate. ENERGY-S3's utility differs slightly from the committed 1.0000, specifically in its classifier score. The variation is consistent with token ordering and model fold assignments changing between runs. That interpretation follows the evaluator's grouping and cross-validation code. The audit did not isolate the contribution of each source of variability.

The refused cases expose actual limits. Reviewed PUB-S3 keeps resolution-time utility at 0.9767, while area counts score 0.3888 and hotspot mapping scores 0.2987. HEALTH-S2 fails its weekly illness and DP workload requirements. CS-S1 fails two required text-related tasks because its selected view cannot answer them. These refusals are appropriate. They establish failure of the tested designs, rather than an impossibility theorem about the scenarios.

For the organiser B2-k baseline, published scenario utility is 0.40 for HEALTH-S1, 0.79 for EDU-S2, 1.00 for HEALTH-S3, 1.00 for ENERGY-S3 and 0.22 for PUB-S3. Our strongest gain over that baseline is HEALTH-S1. The perfect vendor/energy scores do not demonstrate a utility improvement over B2-k. Dataset-wide baseline privacy numbers use different task and release coverage and should not be substituted for scenario-specific comparisons. Our raw baseline also differs from organiser B0, which drops direct identifiers. [Organiser benchmark](../context/proving-ground/docs/BENCHMARK.md)

**Issues requiring fixes**

1. **P1 - A withdrawn table can survive and be released again.** `protect_folder` reuses a directory. Its withhold branch skips the table without removing an earlier CSV or row map. The build copies every CSV except `plan.csv` into the submission. A release-then-withhold probe leaves both withdrawn files present. Use a fresh staging directory, an explicit release-file manifest, and atomic promotion after validation. Existing successful submission directories also lack a version manifest tying them to the most recent attempt. [Protection code](../src/pets_transformer/protect.py) · [Build code](../src/pets_transformer/build.py) · [Probe evidence](../results/audit-2026-11-07/privacy-probes.json)

2. **P1 - The identifier scan does not enforce a release decision.** `score.run` saves the checker's output but does not interpret its findings or failure. `build.run` also ignores scorecard privacy risks when deciding release. In a real probe, adding an old contacts CSV containing a synthetic email to a successful health output produced one EMAIL finding, privacy 1.0000 and a passing red-team gate. The build's copy loop would include that extra file. The organiser checker exits successfully even when it finds identifiers, so return-code handling alone is insufficient. Gate on structured findings, unexpected files, evaluation errors and contract-specific privacy constraints. [Scoring code](../src/pets_transformer/score.py) · [Real scanner/scorer/attack probe](../results/audit-2026-11-07/extra-file-probe.json)

3. **P1 - Detection can downgrade personal event data after direct identifiers are removed.** `detect_dataset` treats a table without recognised person markers as reference data and changes its quasi-identifiers and sensitive attributes to `non_sensitive`. Using the actual health table reduced to visit ID, arrival time, municipality and diagnosis reproduces this for all three latter columns. These still describe personal health events. The downstream code uses those roles to construct generalisation candidates and the k target, so losing those protections is a code-supported consequence. This probe measured detection labels rather than a complete release. Preserve evidence of sensitivity and require positive evidence before classifying a table as public reference data. Shuffling the full health table was a negative control and did not change its labels. [Detector](../src/pets_transformer/detect.py) · [Probe](../results/audit-2026-11-07/detector-shift.json)

4. **P1 - Model validation overlaps training and test identities.** HEALTH-S3's H-U3 fallback uses part of the original table as test data while training the protected model on all protected rows. The scoring entry point does not inject the supplied independent holdout. EDU-U2 attempts to exclude test students using raw student IDs, which fail to match protected tokens. Both bugs are in the organiser evaluator, but our selection and claims inherit them. Evaluate with a frozen identity-aware split or a separate holdout before selecting transformations. [Health evaluator](../data/proving-ground/toolkit/pets_eval/utility/health.py) · [Education evaluator](../data/proving-ground/toolkit/pets_eval/utility/education.py)

5. **P1 for broad safety claims - Declared threats can be absent from a passing gate.** HEALTH-S3 names membership inference and memorisation, yet its released exact clinical rows receive no corresponding test. EDU-S2 lacks attacks using known grades/absence patterns. ENERGY-S3 keeps meter tokens and exact hourly consumption, while its fingerprint check omits consumption patterns. The energy k target groups on timestamp, which many meters share, rather than bounding uniqueness of a person's trajectory. Missing attacks can have null results and still allow overall pass. Define a required attack set from each scenario and distinguish passed, inapplicable, missing and errored evaluations. [Attack gate](../src/pets_transformer/redteam.py) · [HEALTH-S3 evidence](../results/audit-2026-11-07/health-s3/redteam.json) · [ENERGY-S3 evidence](../results/audit-2026-11-07/energy-s3/redteam.json)

6. **P2 - Missing required tasks can count as success.** The build constructs its required-task dictionary from tasks returned by the scorer rather than checking the contract's list. Fault injection with a declared task and an empty utility array produced a passing utility check and submission files. This is a controlled integration probe. The eight real builds returned their task records. Require every declared task to be present with a finite valid score. [Build gate](../src/pets_transformer/build.py) · [Fault-injection evidence](../results/audit-2026-11-07/privacy-probes.json)

7. **P2 - Standalone protection skips repair targets.** The `protect` CLI passes the default `repair_order=None`, which skips the contract's k/l repair. `build` performs repair. Make the entry point's guarantee explicit or apply the complete contract there too. The legacy hour-block PET also writes a block start as an exact hour, while the current repair correctly uses ranges. This discrepancy affects older sweep results and any custom contract using `hour_of_day` with a block greater than one. [CLI](../src/pets_transformer/cli.py) · [Protection](../src/pets_transformer/protect.py) · [PETs](../src/pets_transformer/pets.py)

8. **P2 - Presentation claims lag behind the evidence.** The video and deck still describe clean held-out health detection, although later tuning used held-out results. The video says reconstructed dates are zero, while the measured fraction is 0.0002. It also calls the toolkit result an official score. Update the final materials together with the README's limitations. [Video](../docs/video-script.md) · [Deck outline](../docs/deck-outline.md) · [Detection history](../results/detect/RESULTS.md)

**Usefulness and benchmark dependence**

There is real value in the HEALTH-S1 release. The five task scores reproduce at 0.9979, 0.9549, 0.9578, 1.0000 and 0.9446. These cover median length of stay, diagnosis mix, revisit rates, a visit/lab relationship and arrival-hour distribution. The lab join survives tokenisation. Names, contact details and unused fields are removed. The successful repair retains all 46,398 visits and enforces k of at least five and two distinct diagnosis values on the stated groups, including the lab-presence flag. These group sizes count visit rows and distinct diagnosis-code values. Repeated visits may belong to the same patient, and different codes may describe similar conditions.

The order attack reproduces at 0.0002, compared with the earlier committed 1.0000. News-clip linkage produces zero successful matches in this run. The stronger informed attacker still identifies some records. With generalised values treated as possible matches, it correctly singles out 313 of 46,398 visits, or 0.0067. The headline strict-match variant singles out 0.0971 and correctly identifies 0.0903 of all visits, but excludes coarsened candidates. These are different attacker assumptions and should be reported together. Exact measurements and diagnoses remain disclosed to the controlled recipient. [Fresh health checks](../results/audit-2026-11-07/health-s1/checks/informed_attacker.json)

Independent model evaluation supports useful performance while narrowing the perfect-score claims. AUC measures how well a model ranks positive cases above negative cases, with 0.5 representing chance ranking.

| Model check | Original-training AUC | Protected-training AUC | Utility retention score |
|---|---:|---:|---:|
| HEALTH-S3, separate supplied holdout | 0.7985 | 0.7929 | 0.9811 |
| EDU-S2, identity-aligned original test split | 0.8980 | 0.8952 | 0.9930 |
| EDU-S2, separate supplied holdout | 0.9017 | 0.8702 | 0.9216 |

The health independent check used 2,508 valid holdout visits, and the education holdout used 286 students. A [reproduction script](../results/audit-2026-11-07/reproduce-independent-utility.py) records the model protocol. The supplied health and education holdouts have zero patient/student identity overlap with their training datasets. These are single evaluations with no confidence intervals. The education overlap correction on the original split changes little, while the separate population exposes a larger utility loss. It would be inaccurate to attribute that whole loss to leakage alone. [Health independent result](../results/audit-2026-11-07/health-s3-independent-utility.json) · [Education independent result](../results/audit-2026-11-07/edu-s2-independent-utility.json) · [Holdout identity check](../results/audit-2026-11-07/holdout-overlap.json)

The solution is strongly tailored to this benchmark. The selector directly calls the organiser utility functions while repeatedly choosing columns and transformations on the same data. The repair search selects an order using the same scoring system later reported as evidence. The PET ladder includes choices particularly suitable for the published tasks, such as eight municipalities and hour-of-day extraction. All current detector evaluation sets have also influenced development. The unseen HR export has predictions but no returned organiser score.

Purpose-specific minimisation is appropriate for an agreed sharing purpose. The problem is using that same evaluation as evidence of broad generalisation. The independent model checks show that useful performance can survive outside the tuning rows. They do not establish robustness across different schemas, countries, data distributions or attacker knowledge. A reduced-schema detector probe already fails.

The selector is explainable but heuristic. It greedily removes tables and columns, assumes an ordered PET ladder, and then compares mean utility after repair. This can trade one task against another. The final gate only requires each reported task to exceed 0.5, which is weaker than the selector's initial 0.05 tolerance and the repair search's preferred 0.85 floor. Those different policies should be explicit. Trust level and threat-model text are copied into contracts, but do not select a corresponding policy or attack suite. The generic repair protects one chosen main table and a limited join-presence flag, rather than all possible multi-table or trajectory disclosures.

The fixed age reference is another transfer assumption. The age PET uses the evaluator's default date of 2025-12-31. Relative to age at the visit, 2,492 of 46,398 health rows fall in a different ten-year band before repair. That is a definition difference the release should state. A configurable reference is needed for other periods. [Age-reference check](../results/audit-2026-11-07/health-age-reference.json)

**Assessment against the requested perspectives**

| Perspective | Assessment |
|---|---|
| Correct technical implementation | The normal HEALTH-S1 path works and all current tests pass. Output lifecycle, scan enforcement, missing-task handling and the standalone entry point have concrete defects. |
| Reliable PET choices | Removal of unused fields, keyed join tokens, shuffled rows and targeted generalisation are well matched to HEALTH-S1. Reliability falls when detection loses sensitivity or the scenario requires trajectory, membership or text protections outside the implemented candidate set. |
| Intelligent and explainable innovation | The strongest contribution is the integrated selection, local repair, additional attacks and refusal workflow, with measured reasons per choice. The underlying PETs and greedy search are established techniques. A novel privacy mechanism or general-purpose reasoning system has not been demonstrated. |
| Measured impact | The primary scenario has reproducible improvements over raw data and strong utility relative to B2-k. Independent health and education model checks remain useful. Perfect privacy scores in other domains omit important threats. |
| Honest limitations | README and release-gate notes disclose substantial caveats. Final video/deck need correction. Evidence remains limited to synthetic data, specific tasks and explicit attacker assumptions. |

**Completeness estimates**

The original brief asks for a working prototype demonstrating five elements in one realistic sharing scenario. It does not require all 27 scenarios, a web UI, an LLM or every suggested PET. The estimate gives credit for the implemented prototype and deducts for verification defects and unfinished delivery.

| Original challenge area | Weight | Earned |
|---|---:|---:|
| Detection of sensitive data | 15 | 12 |
| Suitable PET selection and protected output | 20 | 17 |
| Measured risk reduction | 20 | 14 |
| Measured utility preservation | 15 | 13 |
| Clear scenario and honest limitations | 10 | 9 |
| Finished usable demonstration and submission | 20 | 10 |
| Total | 100 | 75 |

The technical and evidence portion earns 65 of 80 points, about 81%. The final-delivery portion earns 10 of 20 because scripts, outlines and evidence exist, but the repository lacks confirmation of final video, slides, submission text and archive. Work completed externally may raise that estimate. [Original brief](../context/brief.md) · [Submission checklist](../team/submission-checklist.md)

Our own estimate uses the current HEALTH-S1 and release-gate plans. Earlier query-vault and other exploratory alternatives are outside that adopted direction. Removing the patient pseudonym was an evidence-based tradeoff after a fingerprint attack, rather than an unfinished feature.

| Current project objective | Weight | Earned |
|---|---:|---:|
| Repeatable build and correct output lifecycle | 25 | 20 |
| Enforced release gate and threat coverage | 20 | 11 |
| Selection, repair and traceable choices | 15 | 12 |
| Independent evaluation and regression confidence | 15 | 9 |
| Explanations and fidelity of evidence | 10 | 9 |
| Reproducible handover and finished demo | 15 | 9 |
| Total | 100 | 70 |

The remaining work with greatest effect is to fix release staging and manifest handling, enforce scanner and task completeness, repair the detector downgrade, freeze independent evaluation splits, and align attack coverage with the chosen scenario. Then update the presentation and finish the private organiser handover and submission. The code licence remains an open team decision. The repository file list contains no tracked proving-ground files, row maps, truth/holdout files or HMAC key files. This check covers tracked paths, rather than a full secret scan of repository history.

The identified implementation defects remain open.

TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0).
