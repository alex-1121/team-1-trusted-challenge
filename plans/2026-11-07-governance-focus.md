# The governance issue: who owns the release decision

Status: proposed, not adopted. Author: Claude Fable 5.1, run by Arda, 7 November 2026, after a Since AI official told the team that the extra mile on TrustED is the governance issue, considered next to the business and technical ones. Three research workers (legal, TrustED data-space, PET practice) each researched and argued a position; this file is the synthesis. Comment as PR review comments or `> note (name):` lines. Nothing here is a team decision until a row lands in `../decisions.md`.

## TL;DR, in plain words

Today the tool decides by itself how much privacy risk is acceptable, and for whom. In a real hospital a named person decides that and answers for it. Our code takes those decisions on its own, and our key-decisions file marks one of them "our choice" and the others "open for the team". That is the governance issue.

The extra mile: the tool writes its choices down, shows them to that person, and refuses to release until they sign. Three parts. A policy file that someone owns. A release record the build writes. A gate that will not write the submission folder while the record is unsigned.

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
| Gate thresholds: order attack 0.05, news 0.0, fingerprint 0.05, band-aware linkage 0.01, plain hash 0.0, utility floor 0.5 per task. Astra's audit notes the 0.5 floor is weaker than the selector's 0.05 tolerance | Controller (data steward or DPO) accepts the risk level; in Finland the permit holder assesses and Findata verifies high-risk results | A policy file with an owner and a reason per value, read by the gate |
| k=5 and l=2 on age band, municipality, arrival hour, lab-presence flag | Controller sets the standard, as a Disclosure Review Board would | Policy file |
| Default contract (known recipient) vs `HEALTH-S1-informed.json` (informed attacker singles out 0.0971 of visits on the default, 0.0 on the informed contract, composite 0.9866 vs 0.9647) | The recipient class and the data use agreement decide; a "safe people, safe setting" judgment | Policy file field `recipient_class`, which selects the contract |
| HMAC key drawn fresh per build, never released, never handed over | Controller is the key custodian; the consequence (no re-linking across releases, no longitudinal study) is a stated choice | Release record: custodian named, destruction logged |
| No patient pseudonym, although the organisers' target suggests one | A purpose decision (the study does not need it); the permit applicant should be able to ask for it knowingly | Policy file, with the fingerprint cost (0.2935 of patients unique) shown |
| Which attacks the gate runs | A gate cannot define its own completeness (Astra P1); the review owner approves the attack list per scenario | Policy file lists the required attacks |
| "Known recipient under agreement" | A contractual obligation on the university: no re-identification, no linkage with the three public sources in the threat model. Technically only detectable, never prevented by us | Release record states it as a detective control |

## 5. Options for the extra mile

Weighed on three points: what it costs if we skip it, what it exposes, and whether it dies with the thing it serves.

**A. Policy file plus release record, enforced by the gate.** `policy/HEALTH-S1.policy.json` separate from the contract: thresholds, k, l, required attacks, recipient class, each with an owner and reason. `build` writes `release_record.json` plus a one-page markdown: dataset hash, recipient, purpose, PETs with parameters and their provenance (organiser suggestion, selector default, team choice), attacks run and results, residual risks with the committed numbers, key custody statement, re-run triggers (new attack, new recipient, new table, threshold change), and an approver block (name, role, date, status unsigned or signed). The gate refuses to write `pets_submission/` while the record is unsigned.
- Cost if skipped: the official named governance as the extra mile; without this, the four open rows (one marked "our choice") stay a weakness a judge can see in our own key-decisions file.
- Exposes: a teammate name as approver in a public repo. No key, no row map, no data. The dataset hash is a hash of the protected output, not of originals.
- Dies with: the gate. Policy sits where it is enforced. Good.

**B. Framing only.** A governance section in the deck, the video and `../docs/guarantee-and-residual-risk.md`: who owns which decision, what the tool proposes, what a human signs.
- Cost if skipped: none beyond A, since A needs this text anyway.
- Exposes: nothing.
- Dies with: the deck. A judge may read it as a claim with nothing behind it.

**C. Usage policy plus signed manifest with a verify script (the data-space shape).** An ODRL-style policy in the release (permission: analyse for the HEALTH-S1 purpose; prohibition: re-identify, link; obligations tagged preventive or detective), a manifest with the contract hash, thresholds, scorecard hashes and the gate verdict, and a `verify` command that re-hashes the folder and fails on tampering. Demo: change one row, verify refuses.
- Cost if skipped: low. It speaks TrustED's vocabulary (audit trail, conditions, enforcement point) but its weakest point is that it is self-attestation; nobody independent certifies the PET was applied.
- Exposes: hashes of protected files. Fine.
- Dies with: a separate script that can rot after Sunday.

**Recommendation (author's reading, for the team to overrule):** build A, with B as its text. Take from C only the manifest hashes inside the release record if an hour is left; skip the ODRL policy and the verify script. A is the one that changes what the gate does, which is the difference between a governance claim and a governance control.

## 6. The business angle, in the same frame

- The buyer and the accountable party is the data controller: the hospital's data steward or data protection officer. Findata and the ICO both place responsibility for anonymity on the permit holder or controller. A tool vendor cannot carry it.
- So the product is a tool the controller runs where the data sits, which produces evidence for a human sign-off. That matches the read-only database idea in PR #37 (the tool connects at the provider; "data never leaves" holds only if it runs there). It also keeps us out of the processor role under GDPR Art. 28, which a hackathon team cannot credibly fill.
- Say in the deck: "The tool proposes, measures and refuses. A named person approves." Never say the tool made the data anonymous or GDPR compliant (already a rule in `../AGENTS.md`).

## 7. Demo moment (about 60 seconds)

1. Run the gate on the H release with an unsigned record: it refuses and prints the residual risks it wants a human to accept (informed attacker 0.0971, no dates, lab-presence flag visible).
2. Sign the record as the controller's data steward under the default contract: the gate releases, the record shows the approver, the parameters and their provenance.
3. Flip `recipient_class` to a less trusted recipient: the informed contract applies, composite drops to 0.9647, the informed attacker singles out 0.0. The slide says this is the trade-off the controller chooses, with the numbers.

Uses only existing outputs under `../results/`. Nothing in the demo is a new PET.

## 8. What to say honestly

- Approval is a human step we model; in the hackathon a teammate signs. Say so.
- The record is self-attestation. Nobody independent checked that the PETs were applied as written.
- The recipient's obligations (no re-identification, no linkage) are detectable at best, never prevented by our tool.
- The legal mapping is our reading of public sources; the EHDS article quotes and the CJEU holding were not verified against the primary text in the time available.

## 9. Size

S to M for two people, three to five hours: one policy JSON, a loader in `build.py` that refuses without it, a record writer, a signature check that looks for a non-empty approver block, two tests (unsigned refuses, signed releases), text for the deck and the residual-risk doc. No new PET, no change to the selector or the scores. Files touched: `src/pets_transformer/build.py`, `src/pets_transformer/redteam.py` (read thresholds from the policy), new `policy/HEALTH-S1.policy.json`, `tests/`, `docs/guarantee-and-residual-risk.md`, `docs/deck-outline.md`.

## 10. Questions for the team

1. Do we adopt the governance framing as the "extra mile" story, over spending Saturday on Astra's P1 fixes or a second scenario?
2. Who signs the release record in the demo, and with which role name (data steward, DPO)?
3. Does the informed-attacker contract become the default for `recipient_class: external`, with the known-recipient contract reserved for `controlled_research`?
4. Do the gate thresholds move into the policy file as they are, or does the team revisit the 0.5 utility floor at the same time?

## Sources

`../context/brief.md`, `../context/organiser-reply-2026-11-07.md`, `../context/key-decisions.md`, `../context/trusted-project.md`, `../docs/guarantee-and-residual-risk.md`, `../plans/review_by_astra.md`, `../plans/2026-11-07-release-gate.md`, proving-ground `docs/SCENARIOS.md` and `docs/THREAT_MODEL.md`; web: findata.fi (exporting results, 7 May 2026), ico.org.uk (anonymisation: accountability and governance, 10 Oct 2025), census.gov (2020 key parameters, 9 Jun 2021), csrc.nist.gov SP 800-188 (Sep 2023), edpb.europa.eu Guidelines 01/2025, curia.europa.eu press release 107/25, eur-lex Regulation (EU) 2025/327, trustedproject.eu (22 Sep 2026, 2 Apr 2026, 20 Oct 2026), cordis.europa.eu/project/id/101168467, sinceai.ai/hackathon-2026/guide/builders, arxiv 2309.11289 (EDC policy patterns, 2023).

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
