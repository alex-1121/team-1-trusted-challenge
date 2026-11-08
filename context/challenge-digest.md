# Challenge digest - TrustED PETs Transformer

The whole challenge in about 10 minutes. Details live in the files named in each "Source:" line. For the why behind it, read `what-is-expected.md`; for who is judging and what they build, `trusted-project.md`.

## What we must build

The guiding question: "How might we automatically identify privacy risks in a synthetic dataset, select suitable privacy-enhancing transformations and demonstrate that the protected result still supports a defined analytical purpose?"

The final demo must show five things:

1. The data types identified in the original dataset.
2. The PETs selected for each data type.
3. The transformed dataset or the protected view of the data.
4. A comparison of utility before and after the transformation.
5. A clear explanation of the sharing scenario the protected data is suitable for.

The best solutions keep the patterns, distributions, trends and relationships the use case needs. Hiding values alone is not enough.

Source: `brief.md` section 03, `brief-onepager.md` (Final demonstration).

## The data

One synthetic population: 100,000 residents of Southwest Finland. The same people appear in several datasets, so linking datasets is a real risk.

| Dataset | Story | Main tables | Typical PET problems |
|---|---|---|---|
| `health` | Hospital emergency department, 2025 | ed_visits, lab_results, clinical_notes, published_weekly_stats | Birth date inside the ID, rare diagnoses, clinical free text, small cells |
| `mobility` | Travel cards and city bikes, Oct 2025 | taps, cards, bike_trips | A few points single out most cards; home locations; discount types |
| `smart_city` | Wi-Fi sensors and car-park cameras, Nov 2025 | wifi_probes, anpr_parking, footfall_15min | Static MAC addresses, surnames in network names, plates |
| `energy` | Smart meters, winter 2025-26 | meter_readings_hourly, customers | Occupancy and holiday inference, medical-device flag |
| `finance` | Bank cards and transfers, H2 2025 | card_transactions, transfers, customers | Tokenisation, re-linking receipts, sensitive inference from merchants |
| `cyber` | Company security logs, Mar 2026 | proxy_logs, dns_logs, signin_logs, email_gateway | Joins across logs, IP addresses, names in hostnames, secrets in URLs |
| `education` | Upper-secondary and vocational schools, 2022-2025 | course_grades, students, counsellor_notes | Small classes, proxies in course codes, counsellor notes |
| `public_admin` | Service centre feedback and permits, 2024-25 | service_requests, building_permits | Open release of free text, neighbours named, repeat reporters |
| `customer_service` | Telecom contact centre, 2025 | turns, conversations | Redaction benchmark: spoken numbers, spelled emails, passwords, hidden eval split |
| `unseen` | HR/payroll export from a care company | export_2025_q4 | Headers hidden as `c01..c26`: detect every field without labels |

Totals: 4.7 million rows, 475 catalogued columns, 354,000 labelled PII spans in free text, 13 attacker-knowledge files. Each dataset folder has its own `README.md`.

Source: `proving-ground/START_HERE.md` ("One world, ten datasets").

## Seven suggested paths

Teams may combine them.

- Free-text redaction: `customer_service` (hidden eval split), `health/clinical_notes`, `public_admin`.
- Tabular de-identification under linkage attacks: `health/ed_visits`, `finance/customers`, `education/students`.
- Location and trajectory privacy: `mobility`, `smart_city`.
- Pseudonymisation that keeps joins: `cyber`. Detection must still work after protection.
- Differential privacy for published statistics: `health/published_weekly_stats` with `metadata/dp_query_workload_health.json`, or `energy` neighbourhood load.
- Synthetic data with a measured privacy risk: any table; `holdout/` gives the non-members for membership-inference tests.
- Automatic detection: the `unseen` dataset, scored by the organisers.

Source: `proving-ground/START_HERE.md` ("Choose your path").

## How it is measured

Three separate things:

- Self-assessment (ours): `pets-eval scorecard` gives privacy, utility and a composite score. It builds our before/after evidence. It is not the official judging score.
- Official judging: Since AI's existing four criteria (brief section 06), with no weighted rubric. TrustED's own evaluators apply them remotely (sinceai.ai partner page). (1) Technical implementation: correct, reliable PET choices. (2) Innovation: an intelligent, explainable approach. (3) Impact: evidence of reduced disclosure risk with preserved utility. (4) Presentation: clear scenario, before/after comparison, honest limitations.
- Optional organiser checks, on request: a stronger hidden attacker per domain, private labels for `unseen`, hidden eval spans for `customer_service`. Outputs go in a folder `pets_submission/`, and `docs/EVALUATION.md` asks for it in the repository together with the row maps. That collides with the rule never to publish row maps once the repo is public. Open question for the team: ask on the TrustED Discord channel how to hand `pets_submission/` over privately. Until answered, row maps stay out of git.

Scorecard maths: privacy = 1 - (0.5 x worst risk + 0.5 x mean risk). Composite = weighted harmonic mean of privacy (weight 30) and utility (weight 25). Releasing nothing or everything both score low.

Prizes for this challenge: EUR 2,000 / 750 / 250 for the top three.

Source: `proving-ground/START_HERE.md` ("How you are measured"), `proving-ground/docs/EVALUATION.md`, `brief.md` section 06, `team/plan.md` at commit `7d4a45c` (Judging, prizes).

## Baselines to beat

Six reference solutions: B0, B1, B2, B2-k, B3, B4. The scores and what they teach are in `proving-ground/docs/BENCHMARK.md`. It has sections for B0/B2/B2-k per dataset, B1 field detection, B3 differential privacy on the health workload, and B4 synthetic ED visits.

Source: `proving-ground/README.md`, `proving-ground/docs/BENCHMARK.md`.

## Rules that bite

- Deadline: Sunday 8 November 10:00 Turku time, in sinceai.app. Hard.
- Demo video: a YouTube link, public or unlisted, ideally under 2 minutes. YouTube is the only accepted format.
- Source code zip: up to 100 MB, without data files or node_modules.
- Builder vote card: voters see only the tagline, the first lines of the description, the demo video, the deck and five tech chips. They never see the repo.
- Support: Since AI organisers, event mentors and the event Discord (brief section 08). TrustED itself answers on its Discord channel only, no stand.
- Row maps: `rowmap_*.csv` are never published. We also keep `truth/` and `holdout/` out of the repo and the zip.
- Licence line on anything we publish: "TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0)".
- Say what the guarantee is. "Anonymised" and "differentially private" need a method and parameters.

Source: `../team/submission-checklist.md`, `team/plan.md` at commit `7d4a45c`, `proving-ground/START_HERE.md` ("Rules of the road"), `proving-ground/docs/EVALUATION.md`.

## Quickstart commands

Run from `data/proving-ground/` after the data is restored (see `../data/README.md`). The first command installs the `pets-eval` CLI; Python 3.10 or newer.

```bash
pip install -e ./toolkit
python3 examples/quickstart.py
pets-eval scenarios
pets-eval tasks --dataset finance
pets-eval check results/quickstart
pets-eval scorecard --original data/health --protected my_out/health --scenario HEALTH-S1
```

What they do: install the CLI; protect `health/ed_visits` for scenario HEALTH-S1 and write a scorecard; list the 27 sharing scenarios; list the utility tasks of a dataset; scan an output for residual identifiers; score our own protected output.

Read every CSV with `dtype=str` first. Phone numbers, postcodes and identifiers break when parsed as numbers.

Source: `proving-ground/START_HERE.md` ("Ten-minute quickstart").
