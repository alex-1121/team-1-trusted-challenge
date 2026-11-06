# TrustED, the project behind the challenge

What the real TrustED project is, what it builds, where it stands in November 2026, and what that tells us about the people who will evaluate our work. Researched on 2026-11-06 from the project site and public records; each claim carries a source number from the list at the end. Lines marked (inferred) are our reading, not a TrustED statement.

## In one paragraph

TrustED is a Horizon Europe cybersecurity project (grant agreement 101168467, call HORIZON-CL3-2023-CS-01, topic "Privacy-preserving and identity management technologies", an Innovation Action). Full title: "Enabling Trustworthy European Data Spaces through Self-Sovereign Identity and Privacy Preserving Technologies". It runs from 1 October 2024 to 30 September 2027, so the hackathon falls in month 26 of 36. The coordinator is Gradiant (Vigo, Spain); the challenge brief names Gradiant as coordinator and TREE (Tree Technology) as co-funding partner, which matches the public record. Partner contributions on CORDIS add up to roughly EUR 4 million. [1][2][3]

The project is not about synthetic data or anonymising files for release. It builds two services for personal data inside European data spaces: a federated learning service wrapped in privacy-enhancing technologies, and a self-sovereign identity service built on the EU digital identity wallet. Both promise guarantees that go beyond what GDPR, eIDAS 2 and the EUDI wallet require. [2]

## Partners

Ten consortium members from Spain, Italy, Portugal, Germany and Turkey, plus one associated partner. No Finnish organisation is in the consortium, and no page on the site mentions Turku or Since AI. The hackathon link runs through the project's communication team (the video greeting comes from the project's communication and dissemination manager; the brief's coordination contact sits with the project, not on site). [1][2][4]

| Partner | Country | Role in TrustED |
|---|---|---|
| Gradiant | Spain | Coordinator, research centre |
| Tree Technology (TREE) | Spain | SME, AI, big data, cybersecurity; named co-funding partner in the brief |
| Fundacion Cibervoluntarios | Spain | NGO, runs the volunteering pilot |
| TINEXTA InfoCert | Italy | Qualified trust service provider, attribute issuance |
| CyberSocial Lab | Italy | Ethics and law, consent and selective-disclosure system |
| Fraunhofer ISST | Germany | Data space architecture, EUDI wallet design, federated learning for health |
| Fraunhofer AISEC | Germany | Security, publishes the libbbs library |
| Promptly Health | Portugal | Decentralised clinical data libraries (OMOP, FHIR) |
| Sestek | Turkey | Speech and biometrics |
| ULS Coimbra | Portugal | Clinical partner, hospital pilot |
| Fondazione Mondo Digitale | Italy | Associated partner |

Data-provider collaborators: ELSAN (France) and HM Hospitales (Spain). Sister projects whose components it reuses: LICORICE, CONSENTIS, PRIVIDEMA, RECITALS. [1][2]

## What they are building

- A minimum viable data space on the Eclipse Dataspace Components framework, following Gaia-X and the IDSA data space protocol. [2][3]
- An identity layer: an EUDI-compliant wallet for verifiable credentials, selective disclosure with BBS+ signatures (open-source libbbs), zero-knowledge proofs (for example "no relevant convictions" without showing the record), AI document validation and biometrics, and a consent system that keeps a cryptographic proof of the policy a person accepted. [2][5][6][8]
- A federated learning layer for clinical data: hospitals train a shared model without moving records. Its named building block is SASS, Secure Aggregation with Secret Sharing (Shamir threshold sharing, distributed aggregators, a minimum group size), combined with differential privacy and trusted execution environments. The project itself lists SASS's limits: small groups leak through the aggregate, collusion assumptions, communication overhead, and poisoned inputs that need validation. [2][6][10]
- Their PET vocabulary: zero-knowledge proofs, homomorphic encryption, differential privacy, secure multiparty computation, trusted execution environments, federated learning, secret sharing. Masking, generalisation, tokenisation and synthetic data (techniques the challenge lists) and k-anonymity do not appear on the site. [2][10][11]

## Pilots

- Spain, social sector: Fundacion Cibervoluntarios issued a digital volunteering credential to more than 70 volunteers; a trusted authority confirms a clean criminal record by zero-knowledge proof. Measured usability, privacy and trust. [4][8][12]
- Portugal, health: ULS Coimbra validated the federated learning platform on predicting viral respiratory infections (flu, COVID-19, RSV), through interviews with researchers, technical staff and clinicians. [4][8][12]
- Planned scenarios: public services, finance and healthcare; one example is proving a payslip for a loan without handing over the document. [7]

## Where they stand now

- Phase: past development, in real-world validation. The pilots were launched at the 30 June 2026 meeting in Dortmund, where partners validated phase-one results. [4]
- Recent output: 20 Oct 2026 SASS explainer; 22 Sep 2026 article on data minimisation, selective disclosure and ZKP; 8 Sep 2026 CORDIS "Project of the Month"; 13 Jul 2026 pilot write-up; 2 Apr 2026 federated data processing. [5][8][10][12][13]
- Context they build on: EU member states must offer an EUDI wallet by the end of 2026; from 2027 public bodies and some private ones must accept it. [4]
- The project ends 30 September 2027. Public next steps are thin: partners "will define the next steps". No exploitation plan, licence or product roadmap is public. [3][4]

## What this means for our build

The proving ground is Since AI's own work, "inspired by" TrustED, and says so (`proving-ground/docs/LIMITATIONS.md`, last bullet). So we are not expected to plug into TrustED's wallet or federated platform. But TrustED's evaluators will judge us, and their habits of mind are visible in their writing. (inferred, from [5][8][10])

- They think in purposes, not files. Their phrase is "GDPR data minimisation as a technical capability": disclose exactly what a purpose needs, prove the rest. Our scenario-bound PET selection (demo item 5) is the same idea on a single dataset. Lead with the purpose, then the minimal release.
- They distrust aggregates that are too small. Minimum group sizes and differential privacy on aggregates are their own guard rails. Small-cell suppression and stated epsilon will read as fluent to them.
- They expect a stated guarantee with parameters. Their SASS article names its own limits. A residual-risk section that says which attack still works, at what rate, speaks their language.
- Health is their flagship domain. Their central use case is a model trained on hospital data without the records leaving the hospital. The challenge has no federated option, so the nearest matches are the `health` scenarios where the controller releases less than the raw data: published statistics under a stated privacy budget (HEALTH-S2), or a minimised, synthetic or pseudonymised extract for an outside model builder (HEALTH-S3). This is a fit observation, not a decision; the dataset pick is the team's (see `../team/plan.md`).
- Phrases that match their vocabulary and can go into the pitch unchanged in meaning: "prove what needs to be proven", "the data stays under the control of the institution", "data minimisation as a technical capability".

What not to do: do not claim the tool is a TrustED component, do not frame it as federated learning if it is not, and do not use their PET names (SMPC, HE, TEE) for things we did not build.

## Sources

1. https://trustedproject.eu/ (page modified 2026-07-07; latest news item 20 Oct 2026)
2. https://cordis.europa.eu/project/id/101168467 (last update 30 Sep 2026)
3. https://www.isst.fraunhofer.de/en/departments/healthcare/projects/TrustED.html (page dated 2026-05-07)
4. https://trustedproject.eu/dortmund-secure-sovereign-digital-identity/ (30 Jun 2026)
5. https://trustedproject.eu/beyond-all-or-nothing-operationalising-data-minimisation/ (22 Sep 2026)
6. Same as 3, Fraunhofer ISST role
7. https://mondodigitale.org/en/news/digital-trust (4 Sep 2026)
8. https://trustedproject.eu/protecting-sensitive-personal-data-through-federated-data-processing/ (2 Apr 2026)
10. https://trustedproject.eu/sass-secure-aggregation-with-secret-sharing/ (20 Oct 2026)
11. https://www.biometricupdate.com/202609/trusted-tests-whether-europes-digital-identity-model-can-preserve-privacy-in-the-real-world (10 Sep 2026)
12. https://trustedproject.eu/europe-is-building-the-rulebook-for-digital-trust-trusted-is-already-testing-it-on-real-people/ (13 Jul 2026)
13. https://trustedproject.eu/trusted-project-of-the-month/ (8 Sep 2026)

Not covered: the site has no work-package, deliverable or events pages, so deliverable status is unknown. The libbbs repository was not opened. Only the challenge brief (`brief.md`) ties Gradiant and TREE to this hackathon.
