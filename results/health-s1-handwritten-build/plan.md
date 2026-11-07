| table | column | role | pet | params | reason | note |
|---|---|---|---|---|---|---|
| ed_visits | visit_id | record_key | token | {'prefix': 'V'} | Record key, sequential in arrival order: kept as is, sorting by it gives back every arrival date (results/redteam/before-7cf541b.json). A keyed token with the same key as lab_results.visit_id keeps the H-U7 join and carries no order. |  |
| ed_visits | patient_hetu | direct_identifier | drop |  | Direct identifier. A keyed pseudonym would link every visit of a patient, and age band, sex, municipality and the set of arrival hours then single out most repeat patients (results/redteam/before-7cf541b.json). No HEALTH-S1 task needs it: H-U6 reads readmit_30d. Trade-off: no patient-level linkage for the researchers. |  |
| ed_visits | patient_name | direct_identifier | drop |  | Direct identifier; no required task needs it (attacker: record linkage by name, phone or address). |  |
| ed_visits | date_of_birth | quasi_identifier | age_band | {'width': 10, 'also_as': ['age']} | Quasi-identifier; 10-year band written here so the scorer counts it in k, and copied to age for H-U6 (30-day revisit rate by age band). |  |
| ed_visits | sex | quasi_identifier | keep |  | Kept: stratified analysis context; low-cardinality quasi-identifier counted in k. | named rule wins over detected role quasi_identifier |
| ed_visits | phone | direct_identifier | drop |  | Direct identifier; no required task needs it (attacker: record linkage by name, phone or address). |  |
| ed_visits | home_address | direct_identifier | drop |  | Direct identifier; no required task needs it (attacker: record linkage by name, phone or address). |  |
| ed_visits | postcode | quasi_identifier | drop |  | Quasi-identifier finer than needed; municipality serves H-U4 (attacker: linkage to public directory). |  |
| ed_visits | municipality | quasi_identifier | top_n_exact_else_other | {'n': 8} | Eight largest municipalities exact for H-U4 diagnosis mix, rest become other to lift k (attacker: linkage). |  |
| ed_visits | arrival_ts | quasi_identifier | hour_of_day |  | Exact timestamp is a quasi-identifier; hour of day as HH:00 serves H-U8 arrival curve, date dropped (no seasonality study possible). |  |
| ed_visits | arrival_mode | non_sensitive | drop |  | Catalogued quasi-identifier (helicopter and police arrivals are rare); no required task reads it, and dropping it cuts the share of groups with a single diagnosis from 0.2787 (results/checks/l_diversity.json at commit a7c9b76) to 0.1128 (results/checks/l_diversity.json). |  |
| ed_visits | ambulance_unit | technical_identifier | drop |  | Device, staff or foreign-key code; no required task needs it (attacker: linkage). |  |
| ed_visits | triage | non_sensitive | keep |  | Low-risk descriptive or clinical value the study uses. |  |
| ed_visits | chief_complaint | free_text | drop |  | Free text can carry identifying detail; coded fields serve the tasks instead. |  |
| ed_visits | icd10_primary | sensitive_attribute | keep |  | Clinical measurement or diagnosis code the study needs; not an identifier at this granularity. |  |
| ed_visits | icd10_secondary | non_sensitive | keep |  | Low-risk descriptive or clinical value the study uses. |  |
| ed_visits | systolic_bp | sensitive_attribute | keep |  | Clinical measurement or diagnosis code the study needs; not an identifier at this granularity. |  |
| ed_visits | diastolic_bp | sensitive_attribute | keep |  | Clinical measurement or diagnosis code the study needs; not an identifier at this granularity. |  |
| ed_visits | heart_rate | sensitive_attribute | keep |  | Clinical measurement or diagnosis code the study needs; not an identifier at this granularity. |  |
| ed_visits | resp_rate | quasi_identifier | keep |  | Kept: clinical measurement, not an identifier at this granularity. | named rule wins over detected role quasi_identifier |
| ed_visits | temp_c | non_sensitive | keep |  | Low-risk descriptive or clinical value the study uses. |  |
| ed_visits | spo2 | sensitive_attribute | keep |  | Clinical measurement or diagnosis code the study needs; not an identifier at this granularity. |  |
| ed_visits | pain_nrs | sensitive_attribute | keep |  | Clinical measurement or diagnosis code the study needs; not an identifier at this granularity. |  |
| ed_visits | attending_physician_id | technical_identifier | drop |  | Device, staff or foreign-key code; no required task needs it (attacker: linkage). |  |
| ed_visits | attending_physician_name | direct_identifier | drop |  | Direct identifier; no required task needs it (attacker: record linkage by name, phone or address). |  |
| ed_visits | discharge_ts | quasi_identifier | drop |  | Exact timestamp quasi-identifier; length of stay is already in los_minutes for H-U2. |  |
| ed_visits | los_minutes | non_sensitive | keep |  | Low-risk descriptive or clinical value the study uses. |  |
| ed_visits | disposition | non_sensitive | keep |  | Low-risk descriptive or clinical value the study uses. |  |
| ed_visits | readmit_30d | non_sensitive | keep |  | Low-risk descriptive or clinical value the study uses. |  |
| ed_visits | date_of_birth |  | repair:age20 | {'op': 'widen_band', 'width': 20} | At-risk rows only: 10-year age band widened to 20 years (also in age). | 3613 rows (only rows in groups with k<5 or l<2) |
| ed_visits | municipality |  | repair:town_other | {'op': 'set', 'value': 'other'} | At-risk rows only: municipality becomes other. | 2458 rows (only rows in groups with k<5 or l<2) |
| ed_visits | arrival_ts |  | repair:hour3 | {'op': 'widen_hour', 'block': 3} | At-risk rows only: arrival hour widened to a 3-hour block. | 125 rows (only rows in groups with k<5 or l<2) |
| ed_visits | date_of_birth, sex, municipality, arrival_ts |  | repair:suppress |  | Rows still at risk after the ladder: every k column suppressed. | 28 rows (only rows in groups with k<5 or l<2) |
| ed_visits | (row) |  | repair:drop_rows |  | Rows still at risk after suppression are not released. | 0 rows (only rows in groups with k<5 or l<2) |
| lab_results | lab_id | record_key | token | {'prefix': 'L'} | Record key numbered in visit order: kept as is, the first lab id per visit gives back the arrival order. Keyed token, no order. |  |
| lab_results | visit_id | technical_identifier | token | {'prefix': 'V'} | Join key to ed_visits; same keyed token as ed_visits.visit_id, so H-U7 still joins, and no visit order is left. |  |
| lab_results | test_code | non_sensitive | keep |  | Low-risk descriptive or clinical value the study uses. |  |
| lab_results | test_name | non_sensitive | keep |  | Low-risk descriptive or clinical value the study uses. |  |
| lab_results | value | non_sensitive | keep |  | Low-risk descriptive or clinical value the study uses. |  |
| lab_results | unit | non_sensitive | keep |  | Low-risk descriptive or clinical value the study uses. |  |
| lab_results | ref_range | non_sensitive | keep |  | Low-risk descriptive or clinical value the study uses. |  |
| lab_results | abnormal_flag | non_sensitive | keep |  | Low-risk descriptive or clinical value the study uses. |  |
| lab_results | sampled_ts | quasi_identifier | drop |  | Exact timestamp quasi-identifier; no required task needs lab sampling time. |  |
| clinical_notes | note_id | record_key | withhold |  | Free-text notes carry identifying detail; no required task uses them and no redactor is in scope. |  |
| clinical_notes | visit_id | technical_identifier | withhold |  | Free-text notes carry identifying detail; no required task uses them and no redactor is in scope. |  |
| clinical_notes | note_type | non_sensitive | withhold |  | Free-text notes carry identifying detail; no required task uses them and no redactor is in scope. |  |
| clinical_notes | author_staff_id | technical_identifier | withhold |  | Free-text notes carry identifying detail; no required task uses them and no redactor is in scope. |  |
| clinical_notes | author_name | direct_identifier | withhold |  | Free-text notes carry identifying detail; no required task uses them and no redactor is in scope. |  |
| clinical_notes | written_ts | quasi_identifier | withhold |  | Free-text notes carry identifying detail; no required task uses them and no redactor is in scope. |  |
| clinical_notes | language | quasi_identifier | withhold |  | Free-text notes carry identifying detail; no required task uses them and no redactor is in scope. |  |
| clinical_notes | note_text | free_text | withhold |  | Free-text notes carry identifying detail; no required task uses them and no redactor is in scope. |  |
| published_weekly_stats | stat_id | record_key | withhold |  | Aggregate table that would add a second linkage path (week, municipality, age band); no required task uses it. |  |
| published_weekly_stats | week | non_sensitive | withhold |  | Aggregate table that would add a second linkage path (week, municipality, age band); no required task uses it. |  |
| published_weekly_stats | municipality | quasi_identifier | withhold |  | Aggregate table that would add a second linkage path (week, municipality, age band); no required task uses it. |  |
| published_weekly_stats | age_band | non_sensitive | withhold |  | Aggregate table that would add a second linkage path (week, municipality, age band); no required task uses it. |  |
| published_weekly_stats | sex | quasi_identifier | withhold |  | Aggregate table that would add a second linkage path (week, municipality, age band); no required task uses it. |  |
| published_weekly_stats | diagnosis_group | non_sensitive | withhold |  | Aggregate table that would add a second linkage path (week, municipality, age band); no required task uses it. |  |
| published_weekly_stats | visits | sensitive_attribute | withhold |  | Aggregate table that would add a second linkage path (week, municipality, age band); no required task uses it. |  |
