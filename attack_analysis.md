# Attack analysis: what `pets-eval` actually measures

Status: team working note, 2026-11-06. This is an analysis of the organiser toolkit, not a privacy claim about our output.

Scope: the `pets-eval` 1.0.0 package under `data/proving-ground/toolkit/pets_eval/`, plus the metadata, docs and baselines that define how it is used.

Source: TrustED PETs Proving Ground 2026 package, synthetic data by Since AI ry (CC BY 4.0), read 2026-11-06.

## 1. Executive summary

`pets-eval` is not a protection tool. It is a measurement harness. It encodes a specific definition of "good": remove measured re-identification risk, keep the analytical utility the scenario needs, and show both numbers.

The toolkit is also a specification. Reading it tells us what the organisers think a privacy transformation is, what they measure, what they hide from us, and where the scorecard can be gamed.

The central design choice is row alignment. A release with a row map is scored as protected microdata. A release with original record IDs is scored as aligned and the kept IDs are treated as a linkage key. A release with neither is scored as synthetic or aggregate data, and the linkage attack is not run. A good tool should not depend on that fallback.

The central scoring choice is the combination of worst and mean risk. One open door can sink the privacy score. The composite is a harmonic mean, so privacy and utility must both be high. Withholding everything or releasing everything both score low.

The central strategic warning is that the public attacker is a floor, not the target. The organisers hold a stronger hidden attacker for every domain, private labels for the unseen dataset, and hidden eval spans for customer service.

## 2. The package in one page

| Module | Job |
|---|---|
| `io.py` | Finds the package root, loads tables, catalog, scenarios, PII spans, adversary files, truth, holdout, row maps |
| `detect.py` | Scores field classification against `metadata/field_catalog.csv` |
| `text.py` | Scores PII spans and redaction leakage |
| `privacy.py` | k-anonymity, l-diversity, t-closeness, uniqueness, small cells, differencing, DCR, membership inference, trajectory unicity |
| `attacks.py` | Linkage attack, attribute inference, hash dictionary attack, HETU enumeration |
| `scorecard.py` | Orchestrates the privacy plus utility report |
| `check.py` | Regex scan for residual direct identifiers |
| `parse.py` | Tolerant parsers for generalised values and scoring helpers |
| `utility/` | Domain-specific utility tasks for nine datasets |

The CLI has six commands: `scorecard`, `detect`, `text`, `check`, `tasks`, `scenarios`.

The scorecard flow:

1. Load the original dataset folder and the protected folder.
2. Load the field catalog, the chosen scenario, the attack specs, the adversary files, the identity truth, the holdout and the PII spans.
3. For every original table, evaluate the protected version.
4. Collect risk components across all tables.
5. Run the utility tasks for the scenario.
6. Aggregate into privacy, utility and composite, then write `scorecard.json` and `scorecard.html`.

Output conventions:

- Same table file names as the original.
- Keep original column names for the columns kept.
- Generalised values are understood: age bands, truncated postcodes, rounded times, week and month labels, rounded coordinates, three-character ICD-10 codes, diagnosis groups.
- Each released row-level table should have `rowmap_<table>.csv` with `protected_row` and `original_record_id`. It is used only for scoring and must never be published.
- A table with neither a row map nor original record IDs is treated as synthetic data and evaluated with distance-to-closest-record and membership inference against `holdout/`.
- A table that is not released is reported as withheld and contributes no risk.

## 3. What the scorecard evaluates

### 3.1 Residual direct identifiers

For every catalogued `direct_identifier` column present in both original and protected, the scorecard normalises values (lowercase, strip whitespace, hyphens and dots) and computes the share of protected values that also occur anywhere in the original column. The risk is the maximum such share.

It catches names, HETUs, emails, phones, IBANs, cards, plates and addresses that survive verbatim. It does not catch a value that is partially masked, tokenised, or moved into a free-text column. It is also schema-based: it only looks at catalogued column names. Renaming a direct-identifier column can evade it, but the hidden attacker does not use our schema.

### 3.2 Hashed identifiers

`detect_hash_columns` finds columns whose values look like 32, 40 or 64 character hex digests. The scorecard takes candidate values from the original direct and technical identifier columns, generates simple variants (case, separators, country-code forms), hashes them with MD5, SHA-1 or SHA-256, and reports the share of hashed values recovered.

This is a dictionary attack, not a proof. It only detects plain hex hashes. A keyed HMAC passes. A salted hash may pass if the salt is not in the candidate set, but a salt is not a substitute for a secret key. Base64, UUIDs and other encodings are not even detected.

The lesson: plain hashing is not anonymisation, and HETU is trivially enumerable because it encodes birth date and sex. The toolkit ships `enumerate_hetu` to make that point.

### 3.3 k-anonymity on retained quasi-identifiers

For every catalogued `quasi_identifier` column kept, the scorecard computes equivalence classes by hashing the tuple of stringified values. It reports minimum k, median k, the share of rows in classes below 2, 5 and 10, and the share of singleton classes. The risk component is the share of rows with k < 5.

Two details matter:

- Only the QIs kept are used. Dropping a QI improves the measured k, even if the attacker has that QI from elsewhere.
- If there is no row alignment, the k risk is removed from the score and only reported. That is reasonable for synthetic data, but it means a row-level release without a row map gets its k-anonymity ignored.

l-diversity is computed when a sensitive attribute is present, but it is reported, not scored. t-closeness is implemented but not called by the scorecard. The headline privacy score is mostly k plus the attacks below.

### 3.4 Linkage and attribute inference

This is the heart of the evaluation. `attacks.py` implements a background-knowledge linkage attack.

The attacker file has rows describing people the attacker knows something about. A truth file maps attacker rows to person IDs. The identity truth maps original record IDs to person IDs. The row map maps protected rows to original records. The attack intersects candidate sets across quasi-identifiers that survived into the protected table.

The QI kinds are rich:

| Kind | Matching |
|---|---|
| `exact` | Normalised string equality |
| `name` | Token sets, longest token or surname blocking, initials allowed |
| `postcode` | Numeric prefix matching, with the protected value's length deciding the prefix |
| `age` | Intervals from exact age, age band, birth year or birth date, with tolerance |
| `sex` | Finnish and English variants |
| `time` | Intervals from exact timestamps, rounded times, days, weeks, months, years, with attack windows |
| `geo` | Haversine distance within a tolerance derived from the protected coordinate precision |
| `number` | Relative tolerance |
| `suffix` | Last n digits, for card or account fragments |

The attack intersects candidate sets across all usable QIs. If the final candidate set has exactly one row, the attacker makes a unique claim.

Main metrics:

- `reidentification_rate`: correct unique claims divided by attacker targets present in the data.
- `claim_precision`: correct claims divided by all unique claims.
- `share_targets_in_candidate_set_le5`: how often the attacker narrows to five or fewer.
- `median_candidate_set`: how much ambiguity remains.
- `attribute_inference`: when the candidate set agrees on a sensitive value, whether that value is correct, compared with a majority-guess base rate. The risk is the advantage over that base rate.

The attack runs on the protected table and on the original table. That gives a baseline and a `risk_reduction`. The worst of re-identification and attribute-inference advantage becomes the table's linkage risk.

`metadata/attack_specs.json` defines which attacker columns match which protected columns, how loosely, and which column is sensitive. The scenario's `threat_model` text selects which adversaries to use. If every column an attack needs is removed, the attack returns zero with a note. If some QIs remain, those are used.

Important limits:

- The attack only counts a claim when the candidate set is exactly one row. If the candidate set is two rows belonging to the same person, it does not count as a re-identification unless an `entity` column groups rows of one subject.
- It samples at most 3,000 attacker rows.
- It does not model cross-table linkage, composition of multiple releases, or an attacker with a QI that is not in the spec.

Those are exactly the gaps a stronger hidden attacker can exploit.

### 3.5 Free-text leakage

For each catalogued `free_text` column, the scorecard loads the gold PII spans, aligns protected rows through the row map, and checks whether each gold span's text still appears in the protected text. Values are normalised (lowercase, separators stripped) and phone numbers get country-code variants. Values shorter than three characters are skipped.

It reports overall leakage, character-weighted leakage, and `identifying_leakage_rate`, which restricts to labels that identify or single out a person: PERSON, NATIONAL_ID, EMAIL, PHONE, ADDRESS, IBAN, PAYMENT_CARD, ACCOUNT_NUMBER, IP_ADDRESS, LICENSE_PLATE, USERNAME, SECRET, DEVICE_ID, PROPERTY_ID, URL. The worst identifying leakage across free-text columns becomes the risk.

This is a substring test. A typed placeholder passes. A surrogate that changes the value passes. A paraphrase passes. A partially masked value may still leak if enough of the original substring remains. It does not test whether the text remains re-identifiable through context, style, or combinations of non-PII facts.

If the free-text column is withheld, leakage is zero. If there is no row map, it is not evaluated. Both are sensible scoring conventions with obvious gaming potential.

### 3.6 Trajectory unicity

For the four trajectory specs in `attack_specs.json` (mobility taps, bike trips, Wi-Fi probes, ANPR parking), the scorecard runs a de Montjoye-style unicity test. It samples users, draws p random points from each user's own trace, maps each point to a place cell and a time bin, intersects the sets of users seen at those points, and counts how often exactly one user remains.

The original mobility taps have about 98 percent unicity from four points. If the user column is removed, the scorecard records unicity zero with the note that traces cannot be linked. That is true for the scorecard's model, but only true in reality if the released rows truly cannot be grouped by subject through another key, timing pattern, or linkage.

### 3.7 Synthetic-data checks

When there is no row alignment, the release is treated as synthetic. The scorecard excludes direct identifiers, free text, record keys and technical identifiers, keeps columns with less than 50 percent unique values, and computes:

- Distance to closest record: how close each synthetic row is to the nearest original row.
- Exact copies: the share of synthetic rows at distance zero.
- Nearest-neighbour distance ratio.
- If holdout data exists, the share of synthetic rows closer to training than to holdout, which should be about 0.5.
- Membership inference AUC: can an attacker tell members from non-members by distance to the nearest synthetic row? Advantage is `2 * AUC - 1`.

This is a good test for memorising generators. It is not a test for a generator that preserves rare combinations without copying rows. A synthetic release can pass DCR and MIA and still leak through attribute inference or linkage on generated quasi-identifiers.

### 3.8 The regex scan is reported but not scored

The scorecard runs `check.scan_text` over the first 20,000 rows of every string column and stores `regex_residuals` in the table report. It never adds those hits to `risks`.

The separate `pets-eval check` command is the one that reports residual identifiers, with HETU checksum, IBAN mod-97, Luhn, and IP validation. Phone numbers and plates are pattern-only and can produce false positives.

This is one of the clearest gaps. An identifier that survives in a non-catalogued column, or inside a note that is not marked as free text, can be invisible to the scored risk. Run `check` on the whole output folder anyway, including JSON, HTML and markdown, because reports and metadata can leak too.

## 4. Utility: what "keeping value" actually means

Utility is not "keep all columns". It is "preserve the answers to the questions the scenario needs". There are 6 to 11 tasks per domain, and each one runs the same analysis on the original and the protected tables.

| Family | What it tests | Typical scoring |
|---|---|---|
| Aggregate | Counts, means, medians by group | MAPE with minimum cell sizes, then `1 - error / tolerance` |
| Distribution | Histograms, mixes, category shares | Total variation distance |
| Relationship | Correlations, regression slopes, revisit rates, payday effects | Relative error of the relationship |
| Model | Train on protected, test on original or holdout | AUC or PR-AUC ratio, capped at 1 |
| Detection | Run a reference rule on protected logs | F1 ratio against original |
| Text | Intent classification, topic classification, vocabulary retention | F1 ratio or token retention |

The scoring curve is almost always `max(0, 1 - error / tolerance)`. A tolerance of 0.5 means a 50 percent error scores zero. A tolerance of 0.3 is stricter. The tasks clamp scores to [0, 1]. A task that cannot be answered returns `None`, which becomes zero if the scenario requires it.

The tolerant parsers are the contract. If age is generalised to `30-39`, the task parses the midpoint. If a date is generalised to `2025-03` or `2025-W12`, the task parses it. If a postcode is truncated to `201**` or `201`, the task uses the prefix. If coordinates are rounded, the task grids them. If an ICD-10 code is replaced with a three-character code or a diagnosis group, the health tasks map it. This is a deliberate invitation to generalise rather than suppress.

Several tasks reveal the real expectations:

- Model tasks train on the protected data and test on the original or holdout. A release that destroys predictive signal fails, even if its distributions look similar.
- Cross-table tasks need joins. Health CRP versus temperature needs `lab_results` joined to `ed_visits` by `visit_id`. Education needs `student_id` joins. Cyber needs consistent user pseudonyms across logs. Random per-row tokens break these tasks.
- Text tasks need meaning retention. Customer service vocabulary retention and intent classification, and public-admin topic classification, reward redaction that removes identifiers but keeps ordinary language.
- Detection tasks need the attack signal. Cyber tasks run simple rules on the protected logs and compare F1 with the original. If `src_ip`, `domain` or `upn` is removed, the rules cannot fire.
- Some tasks deliberately want non-personal indicators kept. Cyber U8 rewards keeping attacker IPs, domains, device names and user agents verbatim, because those are indicators of compromise, not personal data. Over-redaction is a utility failure.

This is why the scenario matters. A public dashboard and a controlled research release need different answers. The same column can be suppressed in one and generalised in another.

## 5. How the score is aggregated

Privacy:

```text
privacy = 1 - (0.5 * worst_risk + 0.5 * mean_risk)
```

The worst risk is deliberate. One open door is enough for an attacker, so the score punishes the weakest component heavily. In the B2 health baseline, the privacy score is 0.3554 largely because `ed_visits` has a k < 5 share of 1.0. The free-text leakage on `clinical_notes` is 0.8822. The worst components dominate.

Utility is the mean over the scenario's required tasks, with unanswerable required tasks counted as zero. Optional tasks that are answerable are added to the mean. Optional tasks that are unanswerable are dropped. That last detail is a strategic quirk: withholding data for an optional task can remove it from the denominator, while answering it badly can lower the score.

Composite:

```text
composite = (30 + 25) / (30 / privacy + 25 / utility)
```

If either is zero, the composite is zero. Harmonic means punish imbalance. A privacy score of 0.9 with utility 0.2 is not a good trade. The weights are close, so both matter.

The HTML report is generated from the same JSON. It includes the risk bars, utility bars, table-level details, and a note that the scorecard is a self-assessment and that organisers may use a stronger attacker.

## 6. Detection and span scoring

`pets-eval detect` compares a prediction CSV (`dataset,table,column,privacy_role,subtype`) with the field catalog. It reports per-role precision, recall and F1, macro-F1 over roles that have support, accuracy, sensitive recall, subtype accuracy, a confusion matrix and up to 200 errors. A catalogued column missing from the prediction counts as wrong.

The catalog has 475 columns across nine domains and 171 documented traps. Examples:

- HETU encodes birth date and sex.
- `visit_id` is sequential and reveals arrival order.
- Addresses sometimes contain postcode and city.
- Hostnames contain names.
- Free text hides spoken numbers, spelled emails and secrets in URLs.
- Some columns are redundant with each other.

The unseen dataset has obfuscated headers (`c01..c26`), so column names are not enough. Detection must use values, patterns, cross-column context and domain knowledge.

`pets-eval text` has two modes:

- Span prediction: exact or overlap match, per label and micro, with F2 because a missed identifier is worse than an over-redaction.
- Redacted text: for every gold span, check whether its value survives in the protected text, normalised for case and separators, with phone variants and a minimum length of three characters.

The span labels follow `metadata/pii_span_guidelines.md`. There are 20 labels, including PERSON, NATIONAL_ID, EMAIL, PHONE, ADDRESS, LOCATION, DATE, AGE, IBAN, PAYMENT_CARD, ACCOUNT_NUMBER, IP_ADDRESS, LICENSE_PLATE, ORG, URL, USERNAME, SECRET, HEALTH, DEVICE_ID and PROPERTY_ID. Spoken numbers, spelled-out values, lowercase and misspelled values, and values split across turns all count.

The customer service dataset has a hidden eval split. A redactor tuned to the visible templates will lose points there.

## 7. What this tells us the challenge expects

1. Detection is a first-class deliverable. It is scored separately, and the unseen dataset makes generalisation mandatory.

2. The scenario is part of the specification. The recipient, purpose, trust level and threat model determine which utility tasks are required and which attackers are run. A single fixed transformation cannot be optimal for a public dashboard, a controlled research release, an AI vendor and an internal analytics team.

3. Utility is task-specific, not row-preservation. The tasks reward distributions, relationships, model performance, detection performance, joins and ordinary language. They tolerate generalisation. They do not reward keeping exact values for their own sake.

4. The worst risk dominates. Fixing the average is not enough. One table with k = 1, one leaked identifier, one reversible hash, or one free-text column with high leakage can sink the privacy score.

5. Joins are both a utility requirement and a privacy hazard. Consistent pseudonyms are needed for revisits, lab joins, cross-log detection and cross-table analysis. A global pseudonym is a linkage key. The right design is a keyed pseudonym with a secret, scoped per recipient and per dataset, not a random token and not a plain hash.

6. Free text is the biggest scoring lever. The benchmark says regex redaction misses names, spoken numbers and spelled-out emails. The hidden eval split is where that shows up.

7. The public attacker is a floor, not the target. The organisers hold a stronger hidden attacker for every domain: a data broker, HR knowledge, a colleague, a merchant, a municipal insider. Overfitting to `attack_specs.json` and the public adversary files is explicitly called out as useless.

8. The scorecard is gameable, and the hidden checks are not. Withholding tables, dropping QIs, removing the user column, omitting the row map, renaming identifier columns, or replacing values with surrogates can improve the self-assessment while leaving the data re-identifiable. The optional organiser checks are designed to catch that.

9. Honesty is part of the deliverable. The brief asks for residual risk, not a claim of perfection. "Anonymised", "GDPR compliant" and "differentially private" are claims that require a method and parameters.

## 8. What a great tool must do

A tool that only passes the scorecard is a scorecard optimizer. A tool that is good by construction will also pass the scorecard, because it removes what the scorecard measures and keeps what the tasks need.

### 8.1 Architecture: five stages, not one filter

1. Policy contract. Translate the scenario into a machine-readable contract: recipient, purpose, legal basis, threat model, utility requirements, retention period, allowed joins. For each column: role, sensitivity, whether it is needed, at what resolution, and which transformation is permitted. This is the difference between a demo and a tool.

2. Detection. Combine schema rules, value patterns, validators, statistical checks, cross-column inference and NER for text. Handle the traps: HETU encodes birth date and sex, `visit_id` is sequential, addresses contain postcodes, hostnames contain names, free text hides spoken numbers and spelled emails. Emit confidence, not just labels, and route low-confidence fields to review. The unseen dataset means the detector must work without column names.

3. Transformation. Apply the per-type methods below. Enforce the contract, not just the column list. Check the result against the contract before release.

4. Verification. Run the scorecard, but also run attacks the scorecard does not run: cross-table linkage, composition of two releases, temporal linkage, attribute inference on generated data, text re-identification through context, and a stronger attacker with more background knowledge. Run `pets-eval check` on the whole output. Test on holdout and on data not used to tune.

5. Reporting. State the method and its parameters. State what utility was sacrificed. State which attacks still work and at what rate. Make the result reproducible.

### 8.2 Methods per data type

| Data type | What to do | Why it survives a stronger attacker |
|---|---|---|
| Direct identifiers: name, HETU, email, phone, IBAN, card, plate | Remove, or replace with a keyed pseudonym (HMAC-SHA-256 with a secret key). If joins are needed, scope the key per recipient and per dataset. Never plain hash. | A keyed pseudonym is not reversible by enumeration. A plain hash is. HETU is enumerable, so hashing it is not protection. |
| Quasi-identifiers: birth date, age, sex, postcode, municipality, timestamps, coordinates | Generalise all retained QIs jointly, then suppress or merge until every equivalence class has k at least 5, preferably much larger. Check the combinations, not each column. Use l-diversity and t-closeness where the sensitive attribute is skewed. | The guarantee is about the combination. A stronger attacker with more QIs still cannot single out a record if the retained combinations are genuinely ambiguous. An unmanaged QI can break it, so minimise the retained QI set. |
| Sensitive attributes: diagnosis, income, support level, union fee, fraud flag | Keep only if the purpose needs it. Break the link to the person. Check that the sensitive value is diverse within each QI class. | k-anonymity alone does not stop attribute inference. l-diversity or t-closeness does, within the stated model. |
| Technical identifiers: IP, MAC, hostname, device ID, meter ID, account ID | Keyed pseudonyms, truncation, or prefix-preserving anonymisation only where the analysis needs subnet structure. Strip names embedded in hostnames. | Random tokens break joins; global tokens enable mosaic linkage. Per-recipient keys preserve utility without creating a universal key. |
| Free text: notes, chats, complaints | Hybrid NER plus rules plus validators plus context. Typed placeholders. Recall-first. Handle spoken numbers, spelled emails, partial identifiers, third-party names, secrets in URLs, and values split across turns. | A redactor tuned to templates fails on the hidden eval split. A recall-first redactor with validators and context generalises. |
| Aggregates: counts, means, published tables | Small-cell suppression with secondary suppression, or differential privacy with a stated mechanism, epsilon, delta, unit of privacy and contribution bound. Check overlapping releases for differencing. | Secondary suppression and DP are attacker-independent within the stated model. Suppressing one cell while publishing the margins is not. |
| Trajectories: taps, bike trips, Wi-Fi, ANPR | Coarsen space and time, remove or perturb trip ends near home and work, drop rare trips, aggregate, or do not release subject-level traces. Measure unicity. | The unicity attack is about the number of points needed to single out a subject. Reducing spatial and temporal resolution, and removing the points that anchor identity, raises that number. |
| Cross-table joins | Per-recipient pseudonym domains. No global identifier. Consistent generalisation across tables. | The mosaic effect is the biggest hidden risk. If the same person can be joined across releases, each release's k-anonymity is irrelevant. |
| Synthetic data | Use a generator with a privacy argument (DP training, or strong regularisation plus empirical DCR and MIA testing). Do not copy rows. Test attribute inference and linkage, not just DCR. | DCR and MIA are necessary but not sufficient. A synthetic release can pass both and still leak through generated QIs. |

### 8.3 Principles for robustness against an unseen attacker

Assume the attacker knows the method. Kerckhoffs's principle is explicit in the threat model. Security cannot come from a hidden algorithm, a secret column name, or an unpublished transformation. It can come from a secret key, a formal guarantee, or genuine ambiguity in the released data.

Protect the equivalence class, not the row. Row-level masking is fragile because it leaves the combination intact. If every retained combination maps to a large, diverse class, the attacker's extra knowledge does not help unless it includes a QI that was not managed. That is why the QI set must be minimised and generalised jointly.

Prefer a guarantee over a score. k-anonymity with a stated QI set, l-diversity, t-closeness, or differential privacy with named parameters are guarantees with assumptions. A scorecard number is evidence about one attacker. State the assumptions and the residual risk.

Use the right primitive for the job. Keyed pseudonym for joins. Suppression for direct identifiers. Generalisation for QIs. DP for aggregates. Synthetic data for exploratory release. Redaction for text. No single primitive solves all of them.

Recall before precision in text. A missed identifier is worse than an extra redaction. The span scorer uses F2 for exactly this reason. A redactor that misses one name in a note has leaked a person, while a redactor that over-redacts a product name has lost a little utility.

Test the composition, not just the release. Two releases that are each k = 5 can be joined to k = 1. The toolkit does not test this. A great tool should.

Do not tune to the public attacker. The hidden attacker is the test. Use the public attacker to find weaknesses, not to define the target. If a transformation only works because the public spec happens to use `event_date` and `age_mentioned`, it is not protection.

Separate the evaluation from the objective. The scorecard is a lower bound. It can be gamed by withholding, dropping, or renaming. A great tool reports those temptations and refuses them, because the hidden checks and the demo judging will expose them.

### 8.4 Scorecard loopholes not to rely on

| Loophole | Why it can improve the score | Why it is not protection |
|---|---|---|
| Withhold a table | No risk is computed for it | Utility tasks on it become unanswerable, and the hidden judging sees a missing release |
| Drop quasi-identifiers | k-anonymity improves or is not computed | Utility drops, and the attacker may have the QI from elsewhere |
| Remove the user column | Trajectory unicity becomes zero | The rows may still be groupable by timing, location or another key |
| Omit the row map | Linkage is not evaluated; synthetic tests are used instead | The release can still be linkable in reality |
| Rename identifier columns | Schema-based checks miss them | The hidden attacker does not use our schema |
| Replace values with surrogates | Substring leakage passes | Context, style and combinations can still re-identify |
| Keep the regex scan out of the score | Residual identifiers are not scored | `pets-eval check` and the judges can still find them |
| Optimise only the public attack specs | The measured re-identification falls | The hidden attacker uses different background knowledge |

The pattern is consistent: every loophole trades a measured risk for an unmeasured one. A great tool closes the unmeasured one.

## 9. Blind spots in the evaluation

The scorecard is a lower bound. These are the things it does not test, and therefore the things a great tool must test itself:

- Cross-dataset linkage and the mosaic effect, even though the package is built on one population that appears in several datasets.
- Composition of two releases that are individually protected.
- Attribute inference on tables without an attack spec.
- Free-text re-identification through context, style and non-PII facts, rather than exact substring survival.
- Temporal linkage and event correlation across tables.
- A stronger attacker with different QIs, different auxiliary files, or partial knowledge.
- Differencing between overlapping aggregate releases.
- Residual identifiers in non-catalogued columns, reports, HTML and metadata.
- Synthetic data that preserves rare combinations without copying rows.
- Utility tasks the scenario did not select. A release can preserve the measured tasks and destroy other legitimate uses.

## 10. Practical checklist

- [ ] Write the scenario contract: recipient, purpose, threat model, required utility tasks, legal basis.
- [ ] Produce a field inventory with role, subtype, reason and confidence for every column.
- [ ] Detect text PII at span level, with recall-first scoring and validators.
- [ ] Remove direct identifiers or replace them with keyed pseudonyms.
- [ ] Never plain-hash an identifier. Never hash a HETU.
- [ ] Generalise QIs jointly and enforce k >= 5 on every retained combination.
- [ ] Check l-diversity or t-closeness for sensitive attributes.
- [ ] Keep joins only through scoped, keyed pseudonyms.
- [ ] Redact free text with typed placeholders and test on hidden-style text.
- [ ] Protect trajectories by coarsening space and time, and removing trip ends.
- [ ] Suppress small cells with secondary suppression, or use DP with stated parameters.
- [ ] For synthetic data, test DCR, MIA and linkage, not just DCR.
- [ ] Run `pets-eval scorecard` and `pets-eval check` on the final output.
- [ ] Run at least one attack the toolkit does not run.
- [ ] Report residual risk, utility sacrificed and the method parameters.
- [ ] Never publish row maps, truth files or holdout files.

## Appendix A: formulas

```text
privacy   = 1 - (0.5 * max(risk) + 0.5 * mean(risk))
utility   = mean(required task scores, with unanswerable = 0)
composite = (30 + 25) / (30 / privacy + 25 / utility)
score     = max(0, 1 - error / tolerance)
```

The risk components are the maximum direct-identifier retention, the maximum hash reversal share, the share of rows with k < 5, the worst linkage or attribute-inference rate, the worst free-text identifying leakage, the worst trajectory unicity, and the synthetic exact-copy share or membership-inference advantage.

## Appendix B: file map

All toolkit paths are relative to `data/proving-ground/`.

- `toolkit/pets_eval/scorecard.py` - orchestration and aggregation.
- `toolkit/pets_eval/attacks.py` - linkage, attribute inference, hash attack, HETU enumeration.
- `toolkit/pets_eval/privacy.py` - k, l, t, uniqueness, small cells, differencing, DCR, MIA, unicity.
- `toolkit/pets_eval/text.py` - span scoring and redaction leakage.
- `toolkit/pets_eval/detect.py` - field-role scoring.
- `toolkit/pets_eval/check.py` - regex residual scan.
- `toolkit/pets_eval/parse.py` - tolerant parsers and scoring helpers.
- `toolkit/pets_eval/utility/` - domain utility tasks.
- `metadata/field_catalog.csv` - 475 labelled columns and traps.
- `metadata/scenarios.json` - 27 sharing scenarios with threat models and utility requirements.
- `metadata/attack_specs.json` - 16 linkage attacks and 4 trajectory specs.
- `metadata/pii_spans/` - gold PII spans.
- `metadata/pii_span_guidelines.md` - span annotation rules.
- `docs/EVALUATION.md` - what the scorecard measures and the optional organiser checks.
- `docs/THREAT_MODEL.md` - attackers, capabilities and what counts as a successful attack.
- `docs/BENCHMARK.md` - baselines B0 to B4 and their scores.
- `docs/PET_PLAYBOOK.md` - technique-by-data-type guidance.
