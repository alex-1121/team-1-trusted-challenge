# Plan proposal: "Ask the population, not the person" (DP query vault)

Status: **proposed** (not adopted). Author: Tadek, researched with Claude. Comment with `> note (name):` lines or in the PR.

Related: `../team/plan.md` (schedule, roles, demo requirements), `../context/proving-ground/docs/BENCHMARK.md`, `../context/proving-ground/docs/SCENARIOS.md`.

---

## TL;DR

- People and small businesses (a dentist, a law office) keep their data with us, encrypted.
- Researchers, agencies and analysts never get the data. They **ask questions** and get **differentially private answers**. Differentially private (DP) means aggregates with calibrated noise and a provable cap on how much any one person can affect the answer. The cap is the parameter ε (epsilon).
- Every question goes into a **public log**. Each person has a **privacy wallet** showing how much of their privacy budget has been spent and what they got for it.
- An AI agent turns a plain-English question into a safe query. It **refuses** questions that target individuals or groups too small to protect.
- **Weekend build:** the core on the challenge's **health data**: scenario HEALTH-S2, the 254-query DP workload, and baseline **B3** as the number to beat. Media, PR and counter-disinformation research is the pitch and future use case, not the build.

---

## 1. How we got here (summary of the discussion)

1. **The challenge.** Detect privacy risks in synthetic data, choose privacy-enhancing technologies (PETs), transform the data, and **prove** lower re-identification risk plus kept utility for one sharing scenario. The pack includes 9 datasets from one synthetic population of 100k people, attacker background files with ground truth (`adversary/`, `truth/`), the `pets-eval` scorer, and baselines B0-B4 to beat.
2. **First question: how can companies train AI on one person's or one small clinic's data?** What we found:
   - *Input privacy* (who sees raw data during computation: federated learning, secure enclaves, homomorphic encryption) is a different problem from *output privacy* (what the result reveals: anonymisation, DP, synthetic data). The challenge is mainly about output privacy.
   - Training only small adapters (LoRA) suits weak hardware, small updates and tiny datasets, but **is not a privacy guarantee by itself**.
   - DP needs a crowd. One person or one small clinic is no crowd, so that data only works when pooled across many clinics or used for a model that belongs to that person.
   - "Encrypted on our server, clients hold the keys" is legal: we would be a GDPR Art. 28 processor, which is ordinary SaaS. The data is still personal data, though. The real hurdle is **purpose**: training *our* model on it is a new purpose, and health data needs explicit consent (Art. 9).
   - If users hold the keys, our server can only compute inside an **attested enclave** (AWS Nitro, NVIDIA confidential GPUs, Apple Private Cloud Compute). An attested enclave is sealed hardware that proves which code it runs before a key is released. The honest promise is "our staff can't read it", not "it's never decrypted". Fully homomorphic encryption is still far too slow for training.
3. **Second question: a vault researchers or PR agencies can query**, for example to understand how people take in traditional and new media for counter-disinformation or political communication. Findings:
   - It already exists in part: **Athumi** (a Flemish government data company using Solid pods from Inrupt) and **PORT** (Utrecht's data-donation tool, which processes people's TikTok/YouTube exports in their own browser).
   - Legally we'd be a **data intermediation service** under the Data Governance Act (register with Traficom; neutrality rules). The EU Digital Omnibus may move these rules into the Data Act; still pending.
   - Media habits reveal political opinions (special-category data), so we need explicit consent and a data protection impact assessment.
   - The **EU political advertising regulation (2024/900, applies from 10 Oct 2025)** close to bans political *targeting* with personal data. Meta and Google stopped EU political ads. So: **insights, never audiences**.
4. **What makes it new.** Athumi shares the *data* once consent is given. Synthetic-persona startups (Simile, $100M Feb 2026; Aaru; Toluna; GWI) simulate respondents that aren't grounded in real behaviour and are weak on specific segments. Nobody we found combines:
   - answers-only access with a stated DP guarantee,
   - an AI agent that compiles questions and **refuses** unsafe ones,
   - a public, tamper-evident log of every question,
   - users paid in proportion to the privacy spent on them,
   - (stretch) AI personas calibrated on DP statistics from real consented data, with their error measured against real DP answers.

---

## 2. Does this fit the challenge, or fight it?

Checked against the five required demo items in `../team/plan.md`:

| Brief requires | How this proposal covers it | Strength |
|---|---|---|
| 1. Data types identified | Onboarding step: when a clinic uploads a table, we auto-detect each column (direct identifier, quasi-identifier, Art. 9, free text). Scored with `pets-eval detect` | Medium. Must be built; not the core idea |
| 2. PET per data type | Per column: drop or keyed pseudonym for IDs, generalisation for quasi-identifiers, DP for aggregates. Per question: the agent picks mechanism, ε and contribution bound, and explains why | Strong |
| 3. Transformed data / protected view | Protected view = DP answers, plus a DP weekly dashboard replacing `published_weekly_stats.csv`, which SCENARIOS.md calls "an example of what NOT to publish" | Strong |
| 4. Utility before vs after | Official workload: 254 queries (240 counts, 14 means), scored by `pets_eval.utility.health.evaluate_workload`. B3 utility (BENCHMARK.md): 0.50 at ε=0.5, **0.69 at ε=1**, 0.80 at ε=2 | Strong, measurable |
| 5. Sharing scenario | **HEALTH-S2** (public weekly dashboard; the attacker downloads every release and compares them), plus HEALTH-S1 research questions | Strong |
| Judging: impact | Attacks that succeed on the naive output and fail on ours, measured locally with `truth/` (never committed) | Strong |
| Judging: innovation | Agent with refusals, public question log, privacy wallet | Strong |

**Where it pulls away from the brief:**
- The vault, user-held keys, enclaves and payments are **vision, not buildable or provable by Sunday 10:00**. One slide only.
- Media, PR and political research is **not in the pack's data**. If it dominates the pitch, judges may see us as off-topic, and "political" can unsettle reviewers of an EU project. Frame it as *counter-disinformation research with targeting blocked by design*.
- Teams doing per-column transformation across many datasets will cover more detection. We go deep on one track (DP for published statistics) rather than wide.

**Tadek's read:** this is the brief's own "Differential privacy for published statistics" path from START_HERE.md, with an innovation layer on top. Keep the build on health and the vision to one slide.

---

## 3. Options for the team

- **A. Full proposal:** query vault on health data + agent + attacks + log + wallet. Media use case as the pitch.
- **B. Hybrid (recommended):** a standard detect, select PET, transform pipeline for health data, plus the DP query engine and agent as the strongest module. Covers every brief item and keeps the novel part.
- **C. Drop it:** a conventional transformer across several datasets. This proposal becomes the "future vision" slide.

---

## 4. Build plan (option A or B)

### Architecture

```
upload table --> detect (column types) --> vault (health/ed_visits as the "clinic data")
                                              |
researcher question (plain English)           |
   +-> agent: question -> structured query (same JSON schema as the workload)
            |- purpose check: refuse targeting / individuals / tiny groups (logged)
            +- privacy plan: mechanism, epsilon, contribution bound, expected error
                     |
                     v
            DP engine (person-level Laplace or Gaussian noise, contribution bounding,
                       per-person budget ledger, minimum group size, post-processing)
                     |
                     v
     answer + error bars --> public log (hash-chained) --> person's privacy wallet
```

The LLM only ever sees the **question text and the schema**, never data rows.

### Components, mapped to the roles in `../team/plan.md`

| Role | Component | What | Notes |
|---|---|---|---|
| Detection | `detect/` | Column-type detection for an uploaded table | Start from baseline `b1_detect_rules.py`, improve it, score with `pets-eval detect` |
| Transformation | `engine/` | DP query engine + privacy accountant | Person-level DP, bound each patient's number of visits, split ε across query families sensibly, post-process (no negative counts; weekly totals consistent with monthly). **Goal: beat B3's 0.69 at ε=1** |
| Transformation | `agent/` | Plain-English question to query JSON; purpose check; answerability check | Claude API (Sonnet or Haiku 5.5), or rule-based if the team prefers no external API. Fixed list of allowed query types; refusals logged |
| Evaluation | `attacks/` | (1) Differencing: "count" vs "count minus one person". (2) Averaging repeated weekly releases. (3) Linking a revealed record to a name via `adversary/` | Show each attack working on naive output and on `published_weekly_stats.csv`, then failing on ours. Measured with `truth/` locally |
| Evaluation | `eval/` | Workload score + scorecard; privacy vs utility curve across ε | All slide numbers come from committed JSON (AGENTS.md rule) |
| Story and submission | `ledger/`, `wallet/`, `ui/` | Hash-chained public question log; per-person ε spent and budget left; demo app (Streamlit or a small web page) | Ask, plan, answer, log, wallet, attack tab |
| (stretch) | `personas/` | Personas calibrated on DP statistics; simulated vs real DP answers | Only if everything else is green by Saturday afternoon |

### Timeline (fits the schedule in `../team/plan.md`: video Saturday evening, hard deadline **Sun 10:00**)

| When | Goal |
|---|---|
| **Fri night** | Team picks A, B or C (row in `../decisions.md`). Install toolkit, run `examples/quickstart.py` and baselines, reproduce the B3 numbers. Code skeleton |
| **Sat morning** | DP engine with contribution bounding + accountant; workload score at ε = 0.5 / 1 / 2. Detection started |
| **Sat midday** | Attacks (differencing, repeated releases, linkage) on naive vs DP output. Agent: question to query JSON + refusals |
| **Sat afternoon** | Ledger + wallet + UI wired; first end-to-end run; beat B3; privacy vs utility curve; scorecard HTML |
| **Sat evening** | **Scope freeze.** Record the video (English), deck, README |
| **Sun before 10:00** | Final checks against `../team/submission-checklist.md`, submit in sinceai.app |

### Demo script (about 3 minutes; finals pitch is 4 minutes)

1. **Problem:** the hospital's current weekly dashboard (`published_weekly_stats.csv`). The attack names a patient from small cells and repeated releases.
2. **Upload:** the tool detects column types and shows the PET chosen for each.
3. **Ask:** "How many influenza-like illness visits per week in January among people aged 70+?" The agent shows its plan (ε, expected error) and returns the answer with error bars.
4. **Refuse:** "Which patients in Naantali were admitted with a psychiatric diagnosis?" Refused and logged.
5. **Attack again** on our system: the differencing attack fails.
6. **Utility:** workload error vs ε, ours against B3.
7. **Trust:** the public log and one person's privacy wallet.
8. **Vision slide:** the same engine for small clinics and for media or counter-disinformation research. User-held keys, enclaves, consent, paid participation. Honest limitations.

### Limitations we state up front

- DP answers for small groups are noisy, so some questions get refused. That is by design.
- The guarantee depends on the ε we choose and on the contribution bound. We state both every time (AGENTS.md claim rule).
- Enclaves, user keys and payments are design only, not built.
- The agent can misread a question. Safety comes from the fixed query types and the DP engine, not from the LLM.
- The legal points above are our research, not legal advice.

---

## 5. Questions for the team

1. Option A, B or C?
2. Who owns which component? (See the role mapping above.)
3. Is an external LLM API OK (question text only, never data), or should the agent be local or rule-based?
4. Keep the media/political angle in the pitch, or frame the vision around clinics only?

---

## Sources (from the research)

- EU political advertising regulation 2024/900: [Wikipedia](https://en.wikipedia.org/wiki/Transparency_and_Targeting_of_Political_Advertising_Regulation), [UODO](https://uodo.gov.pl/en/553/2049), [Osborne Clarke](https://marketinglaw.osborneclarke.com/advertising-regulation/new-eu-rules-bring-transparency-to-political-advertising/)
- Data intermediation in Finland: [Traficom](https://traficom.fi/en/data-economy-and-data-intermediation/data-intermediation-services), [European Commission](https://digital-strategy.ec.europa.eu/en/policies/data-intermediary-services)
- Digital Omnibus: [Skadden](https://www.skadden.com/insights/publications/2025/11/commission-proposes-significant-changes-to-eu-digital-rules), [EDPB/EDPS opinion](https://www.edps.europa.eu/system/files/2026-02/edpb-edps_press_release_joint_opinion_on_digital_omnibus_EN.pdf)
- Athumi / Solid: [Inrupt case study](https://inrupt.com/case-study/flanders-strengthens-trusted-data-economy), [Belga](https://belganewsagency.eu/flemish-government-launches-data-company-athumi)
- Data donation (PORT): [arXiv](https://www.arxiv.org/pdf/2110.05154), [Utrecht University](https://www.uu.nl/en/organisation/methodology-and-statistics/data-donation)
- DP query systems: [DP API for platform research](https://arxiv.org/pdf/2505.11577), [OpenDP](https://sdtimes.com/data/microsoft-and-harvard-collaborate-on-differential-privacy), [DPSQL+](https://arxiv.org/abs/2602.22699), [AVEC agent budgets](https://arxiv.org/html/2509.10561v1)
- Synthetic personas market: [2026 market map](https://fish.dog/news/synthetic-research-platforms-the-2026-market-map), [Simile funding](https://leadprysm.com/blog/2026-07-16-synthetic-users-persona-simulation-funding), [pitfalls review](https://skimle.com/blog/synthetic-respondents-in-research-promise-pitfalls-and-when-to-use-in-2026)
- DSA Art. 40 researcher access: [EC FAQ](https://algorithmic-transparency.ec.europa.eu/news/faqs-dsa-data-access-researchers-2025-07-03_en)
