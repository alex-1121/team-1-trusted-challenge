# The governance issue: who owns the release decision

Status: adopted 2026-11-07 in the changed form of option D in section 5 (Arda, following a Fable review, row in `../decisions.md`). Sections 4 to 10 were updated after the review and a reading of the code (see "Changes after the review" at the end). Author: Claude Fable 5.1, run by Arda, 7 November 2026, after a Since AI official told the team that the extra mile on TrustED is the governance issue, considered next to the business and technical ones. Three research workers (legal, TrustED data-space, PET practice) each researched and argued a position; this file is the synthesis. Comment as PR review comments or `> note (name):` lines. Nothing here is a team decision until a row lands in `../decisions.md`.

## TL;DR, in plain words

Today the tool decides by itself how much privacy risk is acceptable, and for whom. In a real hospital a named person decides that and answers for it. Our code takes those decisions on its own, and our key-decisions file marks one of them "our choice" and the others "open for the team". That is the governance issue.

The extra mile: a named person signs the policy that sets the risk limits, and the build refuses to run without that signature or if anything in the policy changed. `build` stays one command. Every release carries a record of the signed policy it was built under.

The record also covers what happens after the files leave: what the recipient may and may not do, and the plain fact that the tool cannot enforce any of it from that point on.

The business side follows. The buyer is the hospital's data steward or data protection officer. The tool runs where the data sits. We sell evidence for a human decision. We do not sell the claim that "the tool made this anonymous".

Terms used below, one line each. Data controller: the organisation that owns the data and answers for it in law, here the hospital. Permit authority: in Finland, Findata, which grants research permits for health data. k=5: every released row shares its identifying values (age band, municipality, arrival hour) with at least four other rows. Patient key: a code that links all visits of one patient. Red-team thresholds: the attack scores above which our gate refuses to release.

## 1. The issue in one paragraph

A privacy-enhancing technique (PET) changes data. Which PET, how hard, and for whom are policy questions: how much re-identification risk is acceptable, against which attacker, for which recipient, under which agreement. Law and standards place those questions with the data controller (in HEALTH-S1, the hospital releasing emergency-department data) and, in Finland, with the permit holder, who assesses the risk of results before export, and Findata, which verifies the high-risk ones. A tool that ships k=5, a 0.5 utility floor and a 0.05 order-attack threshold as code constants has taken that decision away from the people accountable for it, and left no record of who accepted the residual risk. Our build is in exactly that state. Making the decision visible, attributable and enforced is what "governance" means for a PET tool.

## 2. Why we believe this (three lenses, one answer)

Three workers were briefed separately and asked to argue different angles. All three landed on decision ownership. One caveat: the briefs pointed every worker at the same "our choice" rows in `../context/key-decisions.md`, so the convergence is partly our own framing. The supporting facts were found independently.

| Lens | Position in one line | Strongest fact |
|---|---|---|
| Legal (Finnish and EU health data) | The release decision belongs to the controller or access body; the tool must make it reviewable and attributable | Findata: the permit holder is responsible for anonymous results and files a notification on every export (findata.fi, updated 7 May 2026) |
| TrustED data-space | Nothing binds the recipient after release; ship a usage policy and a signed release manifest and say which obligations are enforced and which only detectable | The TrustED article of 22 Sep 2026 lists, among the eIDAS2 wallet principles it builds on, audit trails of "which attributes were shared, with whom, and when" (trustedproject.eu); TrustED's own contribution there is selective disclosure and zero-knowledge proofs |
| PET practice and business | k, l, thresholds and key custody are governance parameters; make them a signed, controller-owned decision | US Census 2020: a policy committee, not the algorithm team, approved epsilon (census.gov, 9 Jun 2021); UK ICO: "You must document your key decisions and the rationale for them" (ico.org.uk, 10 Oct 2025) |

## 3. What the law and the standards say

Each row says whether the worker read the primary text or only a summary.

| Source | What it says for us | Checked how |
|---|---|---|
| Findata, exporting results from the processing environment (findata.fi, updated 7 May 2026) | The permit holder produces anonymous results and runs the risk assessment; only high-risk results go to Findata for verification; a notification is required on every export; the form asks for permit reference, date, environment, risk outcome | Page read |
| UK ICO anonymisation guidance, accountability and governance (ico.org.uk, 10 Oct 2025) | A senior owner for anonymisation decisions; document key decisions and rationale; a DPIA structures the record; open release vs limited access depends on the recipient | Page read in full |
| US Census Bureau, 2020 key parameters (census.gov, 9 Jun 2021) | The Data Stewardship Executive Policy Committee set epsilon 19.61 after reviewing accuracy feedback; it had been 12.2 in the April 2021 demonstration | Page read |
| NIST SP 800-188, De-Identifying Government Datasets (Sep 2023) | The agency chooses the sharing model and the risk goals; it can create a Disclosure Review Board; adopt a standard with measurable performance levels | Abstract only; body not readable |
| EDPB Guidelines 01/2025 on pseudonymisation (Jan 2025, consultation closed 14 Mar 2025) | The controller defines the pseudonymisation domain and holds the additional information (keys) separately | Consultation text; no final version found |
| CJEU C-413/23 P, EDPS v SRB (4 Sep 2025) | Whether pseudonymised data is personal data for a recipient depends on that recipient's means of re-identification | Law-firm summaries only; judgment text not read |
| EHDS Regulation (EU) 2025/327 | Data holder deemed controller for making data available (Art. 74); secondary-use access only through a secure processing environment (Art. 73); Chapter IV applies from 26 March 2029 (Art. 105) | Tool summary of a very long page; article quotes unverified |
| Scenario file, HEALTH-S1 (`SCENARIOS.md` lines 9 to 18) | "Pseudonymised data remains personal data (GDPR Recital 26); health data is Art. 9 special category. Comparable to a permit-based secure processing environment" | Read |
| Since AI builders guide (sinceai.ai/hackathon-2026/guide/builders) | Judges weigh "responsible handling of privacy, security and data" and "real-world relevance and business value"; "Never invent numbers"; no "extra mile" or governance wording | Page read |

## 4. Our build, read as governance decisions in disguise

| What the code does today | Whose decision it is in the HEALTH-S1 world | Where it should live |
|---|---|---|
| Gate thresholds: order attack 0.05, news 0.0, fingerprint 0.05, band-aware linkage 0.01, plain hash 0.0, utility floor 0.5 per task, all constants in `redteam.py` and `build.py`. Astra's audit notes the 0.5 floor is weaker than the selector's 0.05 tolerance | Controller (data steward or DPO) accepts the risk level; in Finland the permit holder assesses and Findata verifies high-risk results | Policy file, each value with an owner and a reason; the constants go away |
| k=5 and l=2 on age band, municipality, arrival hour, lab-presence flag, set in the contract as repair targets. The gate never checks the result | Controller sets the standard, as a Disclosure Review Board would | Policy file states the minimum; the gate checks the measured result |
| Default contract vs `HEALTH-S1-informed.json`. Both are for the same university group in the same controlled setting. They differ in what the attacker is assumed to know: the informed contract assumes the attacker also knows the diagnosis group | The controller, from what the agreement lets it assume about this recipient | Policy field `attacker_assumption`, which selects the contract. Numbers in section 7 |
| HMAC key drawn fresh per build, never released, left on disk in `out/` until the next build overwrites it | Controller decides custody; the consequence (no re-linking across releases, no longitudinal study) is a stated choice | The key stays in memory for the build and is never stored. The record says so, and says that the row maps still link tokens to original ids, so the row maps are what needs custody |
| No patient pseudonym, although the organisers' target suggests one | A purpose decision (the study does not need it); the permit applicant should be able to ask for it knowingly | Policy file, with the fingerprint cost (0.2935 of patients unique) shown |
| Which attacks the gate runs | A gate cannot define its own completeness (Astra P1); the review owner approves the attack list per scenario | Policy file lists the required attacks |
| "Known recipient under agreement" | A contractual obligation on the university: no re-identification, no linkage with the three public sources in the threat model. Technically only detectable, never prevented by us | Release record, post-release section |

## 5. Options for the extra mile

Weighed on three points: what it costs if we skip it, what it exposes, and whether it dies with the thing it serves.

**A. Policy file, release record, and an approval bound to both.** Four pieces.

- *Policy file*, `policy/<scenario>.policy.json`, separate from the contract. It holds the thresholds, the minimum k and l, the required attacks, checks and tasks, the attacks that do not apply and why, the setting, the attacker assumption, and the contracts allowed with the hash of each. Each value carries an owner, a reason and a source (organiser suggestion, selector default, team choice).
- *Release record*, `release_record.json` plus a one-page markdown, written by the build next to a candidate release. It holds the recipient and purpose, the PETs with parameters and their source, the attacks and results, the residual risks with committed numbers (including the `fitness` count selector v2 writes into the contract: the share of rows an attacker could pick out knowing every kept value), the key custody statement, re-run triggers (new attack, new recipient, new table, threshold change), and the hash of every file, of the policy and of the contract. A hash is a fingerprint of a file's contents: change one byte and it no longer matches.
- *Post-release section of the record*: the agreement reference, what the recipient must not do (re-identify, link with the three public sources), which of those duties the tool enforces after release (none), and what would show a breach. One thing already helps here. Each build has its own key, so its tokens appear in no other build. With one build per recipient, and as long as the controller keeps each release, a leaked file with its tokens intact can be matched to the release it came from, and the record says who received that release.
- *Three commands in place of one.* `build` produces the candidate and the unsigned record, and stops. `approve` stores the approver's name, role, date and the hash of the record in a separate file. `release` re-runs the gate on the stored results, recomputes every hash, refuses on any mismatch, and copies into `pets_submission/` only the files the record lists, plus the record, the approval and a release log. The record itself is never edited after `build`.

The commands have to be separate because every build draws a new key and a new row order, so its files differ from the last build's. An approval can only bind to a candidate that already exists. A changed policy or contract therefore means a new build and a new approval.

- Cost if skipped: the official named governance as the extra mile; without this, the four open rows (one marked "our choice") stay a weakness a judge can see in our own key-decisions file.
- Exposes: a teammate name as approver in a public repo, and hashes of files that stay private. No key, no row map, no data.
- Dies with: the gate. Policy sits where it is enforced. Good.

**B. Framing only.** A governance section in the deck, the video and `../docs/guarantee-and-residual-risk.md`: who owns which decision, what the tool proposes, what a human signs.
- Cost if skipped: none beyond A, since A needs this text anyway.
- Exposes: nothing.
- Dies with: the deck. A judge may read it as a claim with nothing behind it.

**C. Usage policy plus signed manifest with a verify script (the data-space shape).** An ODRL-style policy in the release (permission: analyse for the HEALTH-S1 purpose; prohibition: re-identify, link; obligations tagged preventive or detective), a manifest with the contract hash, thresholds, scorecard hashes and the gate verdict, and a `verify` command that re-hashes the folder and fails on tampering. Demo: change one row, verify refuses.
- Cost if skipped: low. It speaks TrustED's vocabulary (audit trail, conditions, enforcement point) but its weakest point is that it is self-attestation; nobody independent certifies the PET was applied.
- Exposes: hashes of protected files. Fine.
- Dies with: a separate script that can rot after Sunday.

**D. Signed policy, one build command (chosen).** The hospital's data steward signs `policy/<scenario>.policy.json` with `ssh-keygen -Y sign` before any build. `build` verifies the signature against the public key in `policy/allowed_signers`, and refuses on a missing signature, a changed byte, a wrong signer, or a contract the policy does not allow. It then writes `release_record.json` next to the output, with the policy hash, the hash of every released file, the recipient, the purpose, the recipient's duties and the line "enforced after release: none".
- Cost if skipped: the same as A.
- Exposes: a public key and a role name in the repo. The private key stays on the signer's machine, never in the repo, the zip or `out/`.
- Dies with: the policy file. A changed policy simply needs a new signature.

**Decision (Arda, 2026-11-07):** the official could not be asked again, so Arda chose to follow a Fable review, which picked decision ownership and option D. A's commands are dropped: they would make the video, deck and README wrong, and signing before the build is what the models in section 3 do. A's point that the commands "have to be separate" holds only for binding an approval to output files. C's ODRL policy and verify script stay dropped.

The sentence for evaluators: "Today's PET tools decide on their own how much residual risk is acceptable and for whom. Ours makes the hospital's data steward sign that decision as a policy before any build, and every release records the signed policy it was built under."

## 6. The business angle, in the same frame

- The buyer and the accountable party is the data controller: the hospital's data steward or data protection officer. Findata and the ICO both place responsibility for anonymity on the permit holder or controller. A tool vendor cannot carry it.
- So the product is a tool the controller runs where the data sits, which produces evidence for a human sign-off. That matches the read-only database idea in PR #37 (the tool connects at the provider; "data never leaves" holds only if it runs there).
- Say in the deck: "The tool proposes, measures and refuses. A named person approves." Never say the tool made the data anonymous or GDPR compliant (already a rule in `../AGENTS.md`).

## 7. Demo moment

1. Run `build` on an unsigned policy: it refuses and says why.
2. Sign the policy as the data steward and run `build`: the gate passes, the files arrive, and `release_record.json` shows the policy, the recipient and the recipient's duties.
3. Change one threshold in the policy and run `build` again: it refuses until the steward signs the new policy. This is the moment that makes the signature a control.
4. Show the choice the owner makes between the two attacker assumptions, inside the same controlled research setting. These are the numbers of the shipped contracts. They change if the selector v2 contract replaces the shipped one (section 9):

| | Shipped default contract | Shipped informed contract |
|---|---|---|
| Composite (self-assessment) | 0.9866 | 0.9647 |
| H-U4 (task score) | 0.9549 | 0.8334 |
| H-U8 (task score) | 0.9446 | 0.8485 |
| Informed attacker, strict match: visits singled out | 0.0971 | 0.0 |
| Informed attacker, coarsened rows count as possible matches: visits singled out | 0.0067 | 0.0 |

Both attacker rows are shown because they are different assumptions. A stricter count belongs on the same slide: with five released columns assumed known (age band, municipality, arrival hour, triage, diagnosis), 0.8803 of `ed_visits` rows sit in groups under 5, against 0.0000 on the three catalogued quasi-identifiers that survive (`scripts/risk_baseline.py`, on branch `selector-v2-measured-risk`, not on main yet). Triage and diagnosis drive that number, and they are what the study needs. Sources: `../results/health-s1-build/` and `../results/health-s1-informed-build/`, `scorecard.json` and `checks/informed_attacker.json`. The demo adds no new PET. Commit the results of the candidate that is released, so every quoted number matches the files.

## 8. What to say honestly

- Signing is a human step we model. In the hackathon the signer is a demo key with the role "data steward (demo)". Say so.
- The signature shows that the holder of that key approved those exact policy bytes before the build. It does not show who holds the key, because it is not a qualified e-signature. It does not show that the PETs were applied correctly, and nothing we ship controls the data afterwards.
- The record is self-attestation. Nobody independent checked that the PETs were applied as written.
- The tool enforces none of the recipient's duties after release. A leak can at best be traced to a release, and only with one build per recipient and the tokens intact.
- A passing gate covers the attacks on the approved list and no others. An attack that does not apply is printed as "not applicable", never as 0.0.
- Without the key nobody can recompute a token, but the row maps still link every token to an original id. They stay with the controller and the organisers, never with a recipient.
- The legal mapping is our reading of public sources. Keep GDPR Art. 28, the EHDS article numbers and the CJEU holding off the stage: they were not verified against the primary text.

## 9. What the code does today, and the build order

Read at commit 721306d. The review did not read the code, so these points are new, except where Astra is named.

- `build.run` is one pass: protect, gate, copy. It has no point at which a human can look, and each run produces different files.
- The gate never checks k or l. It runs five attacks and the utility floor. The scorer's k numbers and the results in `checks/` are written and never read. The proof is in our results: the no-flag build passed the gate with a joined minimum k of 1 (`../results/health-s1-noflag-build/`).
- An attack that returns no value counts as passed (`r["pass"] is not False`). A required task missing from the scorecard is never looked at. A `KeyError` in the checks writes `not_run.txt` and the build carries on.
- An attack that could not run usually reports 0.0, which reads as a pass. On HEALTH-S1 the fingerprint attack shows 0.0 only because no person key is released. On HEALTH-S3 all three linkage attackers show `evaluated: false` under a linkage value of 0.0. `news_linkage` has no value on four of our five scenarios because they have no hour column.
- The copy step takes every CSV in a reused folder except `plan.csv`, so a withdrawn table or a stray file goes along (Astra P1-1, P1-2). It also takes the row maps, which the organisers need and a recipient must never get.
- Thresholds are constants: `GATE` in `redteam.py`, also used by `cli redteam`, and `UTILITY_FLOOR` in `build.py`.
- The HMAC key stays in `out/` after the release. Nothing reads it after protection.
- `results/<run>/` is reused, so a second build overwrites the evidence of the first, and `out/` and `pets_submission/*` are git-ignored, so neither can hold a committed record.

Selector v2 runs in parallel on branch `selector-v2-measured-risk` (plan `2026-11-07-selector-v2-measured-risk.md`, not on main yet) and changes only the choice rule in `selector.py`, its tests and its README section. It leaves `build.py`, `redteam.py`, the gate, the thresholds and the attack list alone, so every point above stays true. Three things connect:

- `TOL`, `RISK_LINE` and the knowable-column rule are policy numbers held as constants in `selector.py`. Keeping them out of the policy file for now means an edit there cannot pretend to change a build. They move after selector v2 lands, in a separate change that passes them to the selector as arguments.
- The contract the policy selects depends on selector v2's ship rule (Arda, 2026-11-07, chat): the gate passes, the organisers' privacy score is at least 1.0 (the shipped score, pending Arda's confirmation of that bar), utility stays within 0.02 of 0.971, and a blind reviewer says GO or RESHAPE with fixes applied. If it fails, the shipped contract stays. The policy names one contract either way, so the release design does not depend on the outcome.
- A re-run of `select --scenario HEALTH-S1` reproduced `contracts/HEALTH-S1.json` byte for byte (selector v2 plan, 2026-11-07), so the shipped contract is selector output with no hand edits. In the record its source is "selector default".

Build order, as built on branch `gate-enforce-checks`:

1. **Gate fixes inside `build`.** One pure check covers group size (k and l, also on the join), checks that did not run, attacks that did not run, required tasks, the identifier scan and scorecard risks, and stray files. The copy step takes only the files the contract names.
2. **Signed policy.** One policy file per scenario we build, holding today's values, so no result moves. `GATE` and `UTILITY_FLOOR` go away. `build` verifies the signature after the input checks and fails closed.
3. **Release record** next to the output, as in option D.
4. **Tests**, one per refusal, plus a run of the gate over the committed results: HEALTH-S1 default and informed, HEALTH-S3, EDU-S2 and ENERGY-S3 pass, PUB-S3 fails on utility, and the no-flag build fails on join k.
5. **After selector v2 lands.** Pass `TOL` and `RISK_LINE` from the policy as selector arguments, and re-sign if the contract changes. The record prints `fitness`, or "not measured" when the contract has none.

No new PET, and no new dependency: OpenSSH is already on the machines we checked.

## 10. Questions for the team

1. Answered: governance is the extra-mile story (Arda, 2026-11-07).
2. Answered for the demo: a demo key with the role "data steward (demo)".
3. Open: which attacker assumption does the HEALTH-S1 policy select? It selects default, today's value, until the team changes it and re-signs. Section 7 has the numbers. One thing to weigh: Arda decided tonight (2026-11-07, chat) that sensitive attributes are the target and never the attacker's key. The author reads that as a rule for the selector's risk measure, which the selector session confirmed. The informed contract assumes the attacker knows the diagnosis group, so it stands as a stricter option on top of that rule.
4. Open: the 0.5 utility floor moves into the policy unchanged. A floor of 0.85, the repair search's own floor, passes the default contract (lowest required task 0.9446) and refuses the informed contract (H-U4 0.8334, H-U8 0.8485). A floor of 0.8 passes both.

## Sources

`../context/brief.md`, `../context/organiser-reply-2026-11-07.md`, `../context/key-decisions.md`, `../context/trusted-project.md`, `../docs/guarantee-and-residual-risk.md`, `../plans/review_by_astra.md`, `../plans/2026-11-07-release-gate.md`, `../src/pets_transformer/build.py`, `redteam.py` and `protect.py`, branch `selector-v2-measured-risk` (its plan and `scripts/risk_baseline.py`), `../tests/test_wiring.py`, `../results/health-s1-build/`, `../results/health-s1-informed-build/`, proving-ground `docs/SCENARIOS.md`, `docs/THREAT_MODEL.md` and `metadata/scenarios.json`; web: findata.fi (exporting results, 7 May 2026), ico.org.uk (anonymisation: accountability and governance, 10 Oct 2025), census.gov (2020 key parameters, 9 Jun 2021), csrc.nist.gov SP 800-188 (Sep 2023), edpb.europa.eu Guidelines 01/2025, curia.europa.eu press release 107/25, eur-lex Regulation (EU) 2025/327, trustedproject.eu (22 Sep 2026, 2 Apr 2026, 20 Oct 2026), cordis.europa.eu/project/id/101168467, sinceai.ai/hackathon-2026/guide/builders, arxiv 2309.11289 (EDC policy patterns, 2023).

Not checked: Finnish Act 552/2019 text (Finlex fetch failed), ISO/IEC 27559 and 20889 text (paywalled), NIST SP 800-188 body, ENISA pseudonymisation reports, EHDS article wording, CJEU judgment text, the TrustED partner page on sinceai.ai, PR #37 content (branch not on main).

TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0)

## Review: Claude Opus 5.5 (judgement lens), 2026-11-07

Reviewed by Claude Opus 5.5, run from Arda's session as a blind judgement reviewer. It did not write the plan and does not know who did. Read: this plan, `plans/how-to-propose-and-review.md`, `context/organiser-reply-2026-11-07.md`, `context/brief.md` section 06, `context/key-decisions.md` sections 2 and 3, and `plans/review_by_astra.md`. No code was read and no web source was opened. Facts were checked by a separate worker (Claude Sonnet, verifier, same day): 15 claims, 3 overstated and corrected in the author's text before this review was appended (the audit-trail quote is an eIDAS2 wallet principle the TrustED article cites, Findata verifies only high-risk results while the permit holder assesses, and only the thresholds row says "our choice"), 1 unverifiable (the official's statement and PR #37), the rest confirmed against the source pages and files. The TL;DR was also rewritten for the plain-words finding below; the rest of the author's text is as reviewed. Nothing here is a team decision.

**Verdict:** RESHAPE. Decision ownership is a sound core and option A is the right shape. But as written the sign-off can be faked by typing a name. It sits on top of a gate that Astra showed can still let extra files through. And it leaves out the half of governance that TrustED's own wording points at: what happens to the data after it leaves the hospital.

**Issue framed narrowly.** The plan treats governance as "who approves before release". TrustED's own words in section 2 ("which attributes were shared, with whom, and when"), plus the scenario file's line that pseudonymised data stays personal data, point just as much at what happens after release: what the recipient may use the data for (purpose limitation), and the fact that the hospital loses control once the files leave. Section 4 reduces this to a single row ("detective control", meaning a breach can be noticed later but never prevented). A judge who knows data spaces may say the team solved approval and skipped the hard part. Fix: keep decision ownership as the headline, and make the release record carry the post-release half in plain fields. Those are the purpose, the recipient and the agreement reference, what the recipient must not do (re-identify, link with the three public sources), which of those duties the tool enforces (none after release), and what would show a breach. That costs one section of the record and no new code path.

**Sign-off is theatre.** Section 9 says the signature check "looks for a non-empty approver block". So any text in a name field releases the data, and a teammate signing in the demo is exactly the paperwork a judge will see through. Fix: the approval stores a hash (a fingerprint of the file contents) of the policy file and the attack results it approves. The gate recomputes that hash and refuses if anything changed after signing. The demo then shows the step that makes it a control: change one threshold after signing, and the gate refuses until someone signs again. That is about 30 extra minutes and turns option C's best idea into part of A. Say on stage that this is a stand-in for a real e-signature, not one.

**Built on leaky gate.** Astra's P1 findings 1 and 2 show the build copies every CSV in the output folder: a withdrawn table or a stray contacts file with an email still reaches `pets_submission/` past a passing gate. A governance gate that a named approver signs, but that releases files nobody approved, is a worse look than having no governance gate, and judges score technical implementation. Fix: make the release record's file list the only thing the build copies (an explicit manifest, built in a fresh staging folder), so the governance work closes Astra P1-1 and part of P1-2 instead of taking Saturday hours from them. Move the thresholds into the policy file with their current values, and leave the 0.5 utility floor inconsistency for a later round (question 4: no change, written down as open).

**Recipient class unsound.** Demo step 3 says a "less trusted recipient" gets the informed contract and the leak "drops to 0.0". The informed contract changes what the attacker is assumed to know, not how far the recipient is trusted. And row-level health data with exact measurements and diagnoses is not something to hand to a less trusted recipient at all under the Findata model the plan cites, where results leave only from a secure environment. Astra also reports two attacker variants (0.0971 singled out strict, 0.0067 correct with coarsened matches). The plan quotes only the strict one and does not show the utility cost of the informed contract (H-U4 0.8334, H-U8 0.8485, from key-decisions 2d). Fix: name the two classes as two attacker assumptions inside the same controlled research setting. Have the tool refuse any public or open class outright. Put both attacker numbers and the two task drops on the slide next to the 0.9647 composite.

**TL;DR needs the pack.** The first screen used "k=5", "patient key", "red-team thresholds", "data controller" and "permit authority" with no explanation. `how-to-propose-and-review.md` sections 1 and 4 ask that a teammate without the data pack can follow the first screen. Fix: rewrite it as "The tool currently decides by itself how much privacy risk is acceptable and for whom. In a real hospital a named person decides that and answers for it. We make the tool write those choices down, show them to that person, and refuse to release until they sign", with the terms explained in a line each below. Also drop the GDPR Art. 28 "processor role" claim and the EHDS article numbers from anything said on stage. Section 8 already admits they were not read in the primary text. (Applied to the TL;DR before this PR; the Art. 28 line in section 6 is left for the team.)

**Options.** A survives, reshaped as above: the policy file, plus a release record that also covers post-release duties and that is the only list of files the build may copy, plus an approval bound to a hash. That stays inside about 4 to 5 hours for two people if the ODRL policy is dropped. B survives only as the text for A, never on its own: without A it is a claim with nothing behind it. From C, keep the hashes and the tamper-refusal demo inside A's gate and drop the separate `verify` script and the ODRL policy file, since both would rot after Sunday and repeat what A does.

Not checked: the code in `build.py` and `redteam.py`, so whether the hash-bound approval and the manifest fit in the stated hours is a judgement, not a measured estimate; whether a TrustED evaluator would actually name post-release control over decision ownership; the EHDS, CJEU, EDPB, NIST and ISO rows beyond their "unverified" labels.

## Changes after the review, 2026-11-07

Made by Claude Opus 5.5, run by Arda, after he asked for the review's fixes to go into the plan. The review above stays as written, so its section numbers and quotes describe the earlier text. Its note that the Art. 28 line is left for the team no longer holds: that line is gone from section 6.

- Taken from the review: approval bound to hashes, a file list as the only thing copied, post-release duties in the record, attacker assumptions in place of recipient classes, both attacker numbers and the task drops in the demo, Art. 28 and EHDS off the stage.
- Different from the review: it suggested the approval could sit on top of the existing gate. The code rules that out, because each build produces different files, so section 5 splits `build`, `approve` and `release`. It also left the 0.5 floor for later; question 4 now gives the numbers for the team to decide.
- New from reading the code: all of section 9's list, in particular that the gate never checks k or l, and that an attack with no value counts as passed. Also the point that per-build tokens can help trace a leak to a release.
- Design premortem: a second blind reviewer (Claude Opus 5.5, run by Arda's session) read the code and found 13 defects in the first version of this update. The author checked the main claims against the code and committed results, and sections 4, 5, 7, 8 and 9 now carry the fixes. Two differ from what the reviewer offered: `release` refuses a dirty submission folder and never clears it, and the repair floor is the higher of 0.85 and the policy floor, so today's results do not move. A required attack's status is read from existing fields, so the gate also works on committed results.
- Facts: a separate reviewer (Claude Sonnet, verifier) checked 17 claims in the first version of this update; 1 wrong and fixed, and the byte comparison of the review section it could not run was done by the author and matched.
- Removed: time estimates. The size section is now a build order.
- Aligned with selector v2 (read from its plan and its session on 2026-11-07, neither on main yet): policy numbers, shipped-contract labels, the `fitness` count in the record, and question 3.
- Adopted form: Arda asked for a Fable reviewer's call and chose to go with it. Option D replaces option A; sections 5, 7, 8, 9 and 10 changed to match. The review above and option A's text stay as history.
