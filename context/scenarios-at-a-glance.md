# The 27 sharing scenarios at a glance

One row per scenario, condensed from `proving-ground/docs/SCENARIOS.md` on 2026-11-06. Use it to shortlist; read the full entry before designing. Rule from the top of that file: a PET choice is right or wrong only for a given recipient and purpose, so pick one scenario per dataset and design for it. `pets-eval scorecard --scenario <ID>` runs that scenario's utility tasks. The privacy targets in the full file are suggestions, not official thresholds. The task IDs mean different things per dataset; `pets-eval tasks --dataset <name>` lists what each one measures.

Terms: DPA is a data processing agreement (the recipient may only process the data for us). MSSP is a managed security service provider. CERT is a national computer emergency response team and ISAC an information-sharing group in one sector. DP is differential privacy. Art. 9 is the GDPR article on special categories of personal data (health, religion and similar), which need extra care.

| ID | Dataset | Recipient and purpose | Utility tasks | Hardest privacy problem |
|---|---|---|---|---|
| HEALTH-S1 | health | University group, controlled research: ED stay, revisits, diagnoses | H-U2, H-U4, H-U6, H-U7, H-U8 | Record linkage on age, sex, municipality, arrival time |
| HEALTH-S2 | health | Anyone, open portal: weekly ED load and illness trends | H-U1, H-U8, H-DP | Small cells and differencing between weekly releases |
| HEALTH-S3 | health | External AI vendor under DPA: train an admission-prediction model | H-U2, H-U3, H-U5 | Membership inference, memorised rare patients in synthetic data |
| MOB-S1 | mobility | Anyone, open data: weekly origin-destination flow matrices | MOB-U1, MOB-U2, MOB-U3 | Outsider sees a neighbour at a stop |
| MOB-S2 | mobility | Planning consultancy under DPA: network redesign from row-level journeys | MOB-U1, MOB-U2, MOB-U4, MOB-U5 | Singling out riders by trajectory |
| MOB-S3 | mobility | University group: bus vs city-bike mode choice | MOB-U4, MOB-U6, MOB-U7, MOB-U8 | Bike GPS end points near homes |
| CITY-S1 | smart_city | Anyone, open data: hourly footfall by zone | CITY-U1, CITY-U5 | Night-time small counts |
| CITY-S2 | smart_city | Retail association under contract: dwell time, repeat visits, parking | CITY-U1 to CITY-U6 | Member's loyalty-app device list plus plate sightings |
| CITY-S3 | smart_city | Police or parking enforcement: bulk plates and payments at one car park | CITY-U3 | Function creep: parking data reused for surveillance |
| ENERGY-S1 | energy | Anyone, open portal: neighbourhood load for planning | ENERGY-U1, ENERGY-U2, ENERGY-U3 | Neighbours differencing against their own consumption |
| ENERGY-S2 | energy | Demand-response aggregator: find and forecast flexible loads | ENERGY-U2, ENERGY-U4, ENERGY-U5, ENERGY-U6 | Absence inference; series must stay linkable over time |
| ENERGY-S3 | energy | University group: heating, payment problems, winter use | ENERGY-U3, ENERGY-U4, ENERGY-U7 | Broker-profile linkage; medical-device flag (Art. 9) |
| FIN-S1 | finance | Bank fraud consortium: pool card transactions across banks | FIN-U1, FIN-U5 | Cross-bank linkability is needed; random tokens destroy it |
| FIN-S2 | finance | External AI vendor: train fraud and spending-category models | FIN-U1, FIN-U4, FIN-U6 | Special-category inference from merchants |
| FIN-S3 | finance | Statistics office, public release: monthly spending by category and region | FIN-U2, FIN-U3, FIN-U6 | Differencing between releases; merchant dominance in cells |
| CYBER-S1 | cyber | External MSSP under DPA: 24/7 threat monitoring | CYBER-U1 to U7, U9, U10, U11 | Learning who is who or what employees browse |
| CYBER-S2 | cyber | National CERT and ISAC peers: share attacker indicators for campaigns C1 and C2 | CYBER-U3, CYBER-U4, CYBER-U8 | Peers must not see staff, customers or network layout; attacker IPs stay exact |
| CYBER-S3 | cyber | Anyone, public download: detection-research benchmark | CYBER-U1, U2, U3, U5, U6, U9, U10 | Outsider identifying employees, browsing, sick leave or an insider |
| EDU-S1 | education | Public: grade, completion and drop-out statistics by school and programme | EDU-U1, EDU-U3, EDU-U5, EDU-U6 | Small schools and programmes; differencing between tables |
| EDU-S2 | education | Ed-tech vendor under DPA: drop-out early-warning model | EDU-U2, EDU-U4 | Classmate-level knowledge; religion and health categories |
| EDU-S3 | education | University group: gender and language grade gaps | EDU-U1, EDU-U3, EDU-U5 | Spontaneous recognition in small schools |
| PUB-S1 | public_admin | Public open portal: citizen feedback requests with free text | PUB-U1 to PUB-U4 | Free text holds most of the value and most of the risk |
| PUB-S2 | public_admin | The service centre's own analysts: workload and response-time dashboards | PUB-U1, PUB-U2, PUB-U5, PUB-U6 | A curious colleague with insider knowledge |
| PUB-S3 | public_admin | University group: response-time differences by area and language | PUB-U1, PUB-U2, PUB-U3 | Linking with forum posts and permit data |
| CS-S1 | customer_service | Cloud AI vendor, possibly outside the EU: topic mining and agent quality | CS-U1, CS-U3, CS-U4, CS-U5 | Vendor staff and model logs see all text |
| CS-S2 | customer_service | Internal data science team: intent classifier and chatbot | CS-U1, CS-U2, CS-U5 | Model memorisation regurgitating identifiers |
| CS-S3 | customer_service | Outsourced QA partner: score 500 conversations a month | CS-U4, CS-U6, CS-U7 | Human auditors recognising neighbours or public figures |

Flags inside the full file:

- CITY-S3: "A good demo explains why the PET answer here is mostly 'share less', not 'transform more'."
- EDU-S1: small schools and programmes are named as the hard part.
- PUB-S1: text is where most value and most risk sit. FIN-S1: linkability across banks is the whole point. CYBER-S1: random per-row tokens make cross-log detection impossible.
- HEALTH-S1 needs a stable patient pseudonym and joinable visit and lab keys.

Source: `proving-ground/docs/SCENARIOS.md` (314 lines). The "hardest privacy problem" column is taken from each scenario's threat-model or notes lines; the file has no column with that name.
