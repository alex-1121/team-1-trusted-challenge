# The governance issue: who owns the release decision

Status: proposed, not adopted. Author: Claude Fable 5.1, run by Arda, 7 November 2026, after a Since AI official told the team that the extra mile on TrustED is the governance issue, considered next to the business and technical ones. Three research workers (legal, TrustED data-space, PET practice) each researched and argued a position; this file is the synthesis. Comment as PR review comments or `> note (name):` lines. Nothing here is a team decision until a row lands in `../decisions.md`.

## TL;DR, in plain words

Our tool takes decisions that are not a tool's to take. k=5, dropping the patient key, the red-team thresholds, the assumption of a "known recipient under agreement": in a real hospital each one is a risk the data controller or the permit authority accepts and signs, and can later be held to. Today the code takes them on its own, and our key-decisions file calls them "our choice" and "open for the team". That is the governance issue.

The extra mile is to make those defaults a human decision the tool enforces. A policy file that someone owns. A release record the build writes. A gate that refuses to write the submission folder until a named approver has accepted the residual risk.

The business side follows. The buyer is the controller's data steward or DPO. The tool runs where the data sits. We sell evidence for a human decision. We do not sell the claim that "the tool made this anonymous".

## 1. The issue in one paragraph

A privacy-enhancing technique (PET) changes data. Which PET, how hard, and for whom are policy questions: how much re-identification risk is acceptable, against which attacker, for which recipient, under which agreement. Law and standards place those questions with the data controller (in HEALTH-S1, the hospital releasing emergency-department data) and, in Finland, with the permit authority Findata, which checks results before they leave the secure environment. A tool that ships k=5, a 0.5 utility floor and a 0.05 order-attack threshold as code constants has taken that decision away from the people accountable for it, and left no record of who accepted the residual risk. Our build is in exactly that state. Making the decision visible, attributable and enforced is what "governance" means for a PET tool.

## 2. Why we believe this (three lenses, one answer)

Three workers were briefed separately and asked to argue different angles. All three landed on decision ownership. One caveat: the briefs pointed every worker at the same "our choice" rows in `../context/key-decisions.md`, so the convergence is partly our own framing. The supporting facts were found independently.

| Lens | Position in one line | Strongest fact |
|---|---|---|
| Legal (Finnish and EU health data) | The release decision belongs to the controller or access body; the tool must make it reviewable and attributable | Findata: the permit holder is responsible for anonymous results and files a notification on every export (findata.fi, updated 7 May 2026) |
| TrustED data-space | Nothing binds the recipient after release; ship a usage policy and a signed release manifest and say which obligations are enforced and which only detectable | TrustED's own words: audit trails of "which attributes were shared, with whom, and when" (trustedproject.eu, 22 Sep 2026) |
| PET practice and business | k, l, thresholds and key custody are governance parameters; make them a signed, controller-owned decision | US Census 2020: a policy committee, not the algorithm team, approved epsilon (census.gov, 9 Jun 2021); UK ICO: "You must document your key decisions and the rationale for them" (ico.org.uk, 10 Oct 2025) |

## 3. What the law and the standards say

Each row says whether the worker read the primary text or only a summary.

| Source | What it says for us | Checked how |
|---|---|---|
| Findata, exporting results from the processing environment (findata.fi, updated 7 May 2026) | The permit holder produces anonymous results; Findata runs a risk-based check; a notification is required on every export; the form asks for permit reference, date, environment, risk outcome | Page read |
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
| Gate thresholds: order attack 0.05, news 0.0, fingerprint 0.05, band-aware linkage 0.01, plain hash 0.0, utility floor 0.5 per task. Astra's audit notes the 0.5 floor is weaker than the selector's 0.05 tolerance | Controller (data steward or DPO) accepts the risk level; in Finland Findata checks the result | A policy file with an owner and a reason per value, read by the gate |
| k=5 and l=2 on age band, municipality, arrival hour, lab-presence flag | Controller sets the standard, as a Disclosure Review Board would | Policy file |
| Default contract (known recipient) vs `HEALTH-S1-informed.json` (informed attacker singles out 0.0971 of visits on the default, 0.0 on the informed contract, composite 0.9866 vs 0.9647) | The recipient class and the data use agreement decide; a "safe people, safe setting" judgment | Policy file field `recipient_class`, which selects the contract |
| HMAC key drawn fresh per build, never released, never handed over | Controller is the key custodian; the consequence (no re-linking across releases, no longitudinal study) is a stated choice | Release record: custodian named, destruction logged |
| No patient pseudonym, although the organisers' target suggests one | A purpose decision (the study does not need it); the permit applicant should be able to ask for it knowingly | Policy file, with the fingerprint cost (0.2935 of patients unique) shown |
| Which attacks the gate runs | A gate cannot define its own completeness (Astra P1); the review owner approves the attack list per scenario | Policy file lists the required attacks |
| "Known recipient under agreement" | A contractual obligation on the university: no re-identification, no linkage with the three public sources in the threat model. Technically only detectable, never prevented by us | Release record states it as a detective control |

## 5. Options for the extra mile

Weighed on three points: what it costs if we skip it, what it exposes, and whether it dies with the thing it serves.

**A. Policy file plus release record, enforced by the gate.** `policy/HEALTH-S1.policy.json` separate from the contract: thresholds, k, l, required attacks, recipient class, each with an owner and reason. `build` writes `release_record.json` plus a one-page markdown: dataset hash, recipient, purpose, PETs with parameters and their provenance (organiser suggestion, selector default, team choice), attacks run and results, residual risks with the committed numbers, key custody statement, re-run triggers (new attack, new recipient, new table, threshold change), and an approver block (name, role, date, status unsigned or signed). The gate refuses to write `pets_submission/` while the record is unsigned.
- Cost if skipped: the official named governance as the extra mile; without this, the four open "our choice" rows stay a weakness a judge can see in our own key-decisions file.
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
