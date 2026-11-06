# Build idea candidates

Status: draft, not adopted. Drafted by Arda's agent on 2026-11-06 from `../context/`. Add your own candidate as a new section, or comment inline with a line starting `> note (name):`. The pick lands as a row in `../decisions.md`.

## How to read this

Every candidate has to cover the four verbs (detect, select, transform, demonstrate) and the five demo items, because the brief requires them whatever we pick (`../context/what-is-expected.md`). The candidates differ in which dataset and scenario carry the demo, where the clever part sits, and what number we can put on a slide. Size is for four people between Friday night and Saturday evening: S fits with slack, M fits if nothing goes wrong, L needs a cut.

A PET (privacy-enhancing technology) is one protection applied to one column or text, such as a keyed pseudonym, an age band or a redaction. B0 to B4 are the organiser baselines in `BENCHMARK.md`: B0 drops direct identifiers, B1 is a rule-based field detector, B2 is classic generalisation and pseudonyms, B2-k is B2 plus suppression until every row shares its values with at least 5 others (k >= 5), B3 is differential privacy on the health query workload.

Facts about the datasets, baselines and scenarios come from the organiser files; the judgement lines are the agent's and are marked as such.

## A. Purpose-bound release for one hospital dataset

- Dataset and scenario: `health`, demo on HEALTH-S1 (controlled research), with HEALTH-S3 (outside vendor trains a model) as the second scenario shown live.
- What we build: a pipeline that classifies every column of `ed_visits`, `lab_results` and `clinical_notes`, then picks a PET per column from a rule table keyed by scenario (keyed pseudonym for patient id so visits and labs still join, age bands, 3-digit postcodes, rounded arrival times, diagnosis groups, typed-placeholder redaction in notes), writes the protected tables, and runs the scorecard.
- The clever part: the selector. The same column gets a different treatment when the recipient changes, and the tool explains why in one line per column. Switching the scenario in the demo and watching the PET table and the scores change is the story.
- Numbers for the slide: privacy and utility vs B0 (0.28 / 1.00 on health) and B2-k (0.52 / 0.44), on the scenario's tasks (HEALTH-S1 utility for B2-k is 0.40, so there is room). Linkage attack rate from the news-clip and directory attackers.
- Why judges like it (agent's reading): it is the literal brief, health is the domain of TrustED's own pilot, and "disclose what the purpose needs" is their language.
- Risks: H-U6 needs a consistent patient pseudonym (or the `readmit_30d` flag) and H-U7 a visit join between `lab_results` and `ed_visits`, so the pseudonym design must be right early; the scorer looks for the pseudonym in the original `patient_hetu` column name. SCENARIOS.md says "pick one scenario per dataset you work on", so showing a second scenario live goes beyond the organisers' suggestion. Clinical notes need real redaction, not regex, or the free-text leakage component stays high.
- Size: M.

## B. Free-text leak hunter

- Dataset and scenario: `customer_service` on CS-S1 (cloud AI vendor, possibly outside the EU, gets transcripts for topic mining), plus `health/clinical_notes` as a second corpus if time allows.
- What we build: a redactor that combines rules (phone, email, HETU (Finnish personal identity code), card, IBAN, plate patterns, spelled-out digits and emails) with a named-entity recognition (NER) model for names and addresses, emits typed placeholders (`[PERSON]`, `[PHONE]`), and runs a validator pass that checks no gold-like value survives. Scored with `pets-eval text` (precision, recall, and F2, a score that weights recall above precision) against the public spans, and on request by the organisers against the hidden eval split.
- The clever part: catching what regex misses. The benchmark says regex redaction misses names, spoken numbers and spelled-out emails, and that "free-text leakage is where most teams can win"; the PET playbook adds lower-case names, third parties' names and passwords typed into chat as common mistakes.
- Numbers for the slide: span recall and F2 vs the regex baseline; the share of gold values surviving before and after; utility on CS-U1, CS-U3, CS-U4, CS-U5 (topic and quality tasks still work on redacted text).
- Why judges like it (agent's reading): the hidden eval split makes the claim testable by the organisers themselves, which is the strongest kind of evidence we can offer.
- Risks: the texts mix Finnish and English, so off-the-shelf English models miss Finnish names and inflected forms; a Finnish-capable model or a gazetteer from the public directory file is needed. Tabular demo items (2, 3) are thin unless we also protect the `conversations` metadata table, and CS-U3 and CS-U4 read `conversations`, so it has to be released anyway. `turns` has 140k rows, so a model pass over all of them needs batching or a GPU.
- Size: M, L with clinical notes.

## C. Detector first, unseen dataset as proof

- Dataset and scenario: the `unseen` HR/payroll export with hidden headers `c01..c26`, plus one labelled dataset for the transformation half (the `education` students table, 5.2k rows, shares several column types with the export: names, HETU, address, phone; agent's reading).
- What we build: a field detector that infers role and subtype from values alone (formats, entropy, value ranges, cross-column checks such as HETU encoding birth date and sex), self-scored with `pets-eval detect` on the nine labelled datasets (the field catalog has no `unseen` rows, so the `unseen` score only comes from the organisers on request); then the same PET rule table as A applied to its own labels.
- The clever part: beating B1 (macro-F1 0.65, sensitive-attribute recall 0.10) with a detector that works without column names, and asking the organisers to score it on the private `unseen` labels.
- Numbers for the slide: macro-F1 and per-role recall vs B1; the organisers' hidden score if they run it.
- Why judges like it (agent's reading): "automatically identify privacy risks" is the first half of the guiding question, and nobody else can fake a hidden-label score.
- Risks: detection alone does not satisfy demo items 3 to 5, so the transformation half must still be real; two datasets means two stories to tell in two minutes. EDU-S2's utility tasks (EDU-U2, EDU-U4) also join `course_grades` (152k rows) and `absences` on `student_id`, so the education half is more than one small table.
- Size: M.

## D. Trajectories that stop pointing home

- Dataset and scenario: `mobility`, MOB-S2 (planning consultancy gets row-level journeys under contract).
- What we build: keyed pseudonyms per card, timestamps rounded to 15 minutes with a secret per-card shift, trip ends snapped to a grid with ends near home suppressed, rare trips dropped; show unicity (4 points single out about 98 % of cards in the raw taps) falling while the origin-destination matrices and network-load tasks stay usable.
- The clever part: a map. Before and after on the same screen is the most visual demo any candidate offers.
- Numbers for the slide: trajectory unicity before and after; MOB-U1, MOB-U2, MOB-U4, MOB-U5 agreement; B2-k's utility on MOB-S2 is 0.35, so beating it with a trajectory-aware method is plausible.
- Why judges like it (agent's reading): the before/after is understandable to a non-expert in ten seconds.
- Risks: 943k taps make iteration slow; MOB-U4 is scored on `bike_trips`, so that table must be protected and released too; MOB-U5 measures home-to-work commuting flows, which suppressing trip ends near home hits directly; unicity is hard to push down without killing the row-level tasks; the builder vote sees the video, so the map must render well in two minutes of screen recording.
- Size: L.

## E. Share the attack, hide the company

- Dataset and scenario: `cyber`, CYBER-S2 (share campaign indicators with the national CERT (computer emergency response team) and ISAC (information sharing and analysis centre) peers) or CYBER-S3 (public detection benchmark).
- What we build: keyed pseudonyms for users and hosts that keep joins across the log tables (sign-in, VPN, proxy, DNS, endpoint alerts, e-mail gateway), prefix-preserving IP anonymisation for internal addresses with attacker IPs kept exact, hostname scrubbing (names hide in hostnames like `LT-AINVIR-0423`), secret stripping from URLs, and a check that the labelled attack campaigns (C1, C2) are still detectable after protection.
- The clever part: proving detection survives. Run the same detection rules on raw and protected logs and show the same alerts fire.
- Numbers for the slide: CYBER-U3, U4, U8 agreement; the staff-directory linkage attack rate before and after (B0 already scores 0.00 worst re-identification on cyber, so this number may not move); B2-k reaches 0.68 utility on CYBER-S2 and 0.66 on CYBER-S3 (0.40 on HEALTH-S1), so the bar is higher here.
- Why judges like it (agent's reading): TrustED is funded under a cybersecurity call, and keeping data "under the control of the individual or institution holding it" is how trade press describes the project (`trusted-project.md`; not TrustED's own words).
- Risks: CYBER-S2's targets ask for no employee identifiers and no internal IPs or hostnames at all, so the join-keeping pseudonyms fit CYBER-S1 or S3 better than S2; fewer places to use AI, so the innovation criterion rests on the detection-survives proof and the explanation; less visual than A or D.
- Size: S to M.

## F. Publish the dashboard with a privacy budget

- Dataset and scenario: `health`, HEALTH-S2 (public weekly dashboard) with the 254-query DP (differential privacy) workload.
- What we build: person-level differential privacy with contribution bounding (a cap on how many visits one patient adds), a workload-aware budget split (more budget to the queries the scenario needs), small-cell suppression with secondary suppression for the published table, and a differencing demo showing that repeated weekly releases do not reveal a suppressed cell.
- The clever part: beating B3's curve (utility 0.69 at epsilon 1; epsilon is the DP privacy-loss budget, lower is stronger) at the same epsilon by spending the budget where the tasks are, and stating the guarantee in full.
- Numbers for the slide: mean relative error and utility vs B3 at equal epsilon; H-U1, H-U8, H-DP.
- Why judges like it (agent's reading): minimum group sizes and DP on aggregates are the exact guard rails TrustED writes about for its own secure aggregation.
- Risks: narrow; the detect and transform verbs are thin on an aggregate table, so pair it with A's pipeline on `ed_visits` or it fails demo items 1 to 3 on its own. In the toolkit (`../data/proving-ground/toolkit/pets_eval/utility/health.py`, local copy), H-U1 and H-U8 are computed from a row-level `ed_visits` in the protected folder; `dp_answers.csv` only feeds H-DP. An aggregate-only release therefore scores H-U1 and H-U8 as not answerable (0), so HEALTH-S2 utility tops out at about a third.
- Size: S alone, M combined with A.

## Comparison

| | Dataset | Visual demo | AI needed | Hidden organiser check available | Fit with TrustED's own work | Size |
|---|---|---|---|---|---|---|
| A purpose-bound release | health | scenario switch | some (notes) | hidden attacker | high (health pilot, purpose) | M |
| B leak hunter | customer_service | text diff | yes (NER model) | yes (eval split) | medium | M to L |
| C detector first | unseen + education | tables | some | yes (private labels) | medium | M |
| D trajectories | mobility | map | little | hidden attacker | low | L |
| E share the attack | cyber | log diff | little | hidden attacker | high (cybersecurity call) | S to M |
| F privacy budget | health stats | charts | none | none | high (aggregates) | S, M with A |

## Recommendation (agent's, for the team to overrule)

A as the spine, with F folded in as the second scenario instead of HEALTH-S3: one dataset, one tool, two recipients (a research group gets row-level data with a keyed pseudonym and bands; the public gets a dashboard under a stated epsilon). It covers all four verbs on one story, it is the organisers' own quickstart example extended, the scorecard can score both scenarios (one `--scenario` per run, so two runs and two protected folders; see F's risk on H-U1 and H-U8), and it speaks to what TrustED's evaluators build. B is the strongest standalone alternative if the team has someone comfortable with Finnish text models, because the hidden eval split gives evidence nobody can dispute.

Within A, the free-text module on `clinical_notes` is the cut line: ship rules only on Saturday morning, add a model only if the tabular half is done by noon.

Suggested timing, whatever we pick: the key and join design first (for A, the stable patient pseudonym), scorecard running on raw data by Saturday 09:00, video script by Saturday 18:00.

Sources: `../context/what-is-expected.md`, `../context/trusted-project.md`, `../context/scenarios-at-a-glance.md`, `../context/proving-ground/docs/BENCHMARK.md`, `../context/proving-ground/docs/SCENARIOS.md`, `../context/proving-ground/docs/EVALUATION.md`, `../context/proving-ground/docs/DATA_DICTIONARY.md`, `../context/proving-ground/docs/PET_PLAYBOOK.md`, `../context/proving-ground/docs/THREAT_MODEL.md`, `../context/proving-ground/START_HERE.md`, and the local toolkit source under `../data/proving-ground/toolkit/` (gitignored, restore per `../data/README.md`).
