| table | column | role | pet | params | reason | note |
|---|---|---|---|---|---|---|
| building_permits | permit_id | record_key | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (PUB-U1 1.0000, PUB-U2 1.0000, PUB-U3 1.0000). |  |
| building_permits | submitted_date | quasi_identifier | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (PUB-U1 1.0000, PUB-U2 1.0000, PUB-U3 1.0000). |  |
| building_permits | applicant_type | non_sensitive | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (PUB-U1 1.0000, PUB-U2 1.0000, PUB-U3 1.0000). |  |
| building_permits | applicant_name | direct_identifier | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (PUB-U1 1.0000, PUB-U2 1.0000, PUB-U3 1.0000). |  |
| building_permits | applicant_hetu | direct_identifier | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (PUB-U1 1.0000, PUB-U2 1.0000, PUB-U3 1.0000). |  |
| building_permits | applicant_business_id | non_sensitive | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (PUB-U1 1.0000, PUB-U2 1.0000, PUB-U3 1.0000). |  |
| building_permits | property_id | non_sensitive | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (PUB-U1 1.0000, PUB-U2 1.0000, PUB-U3 1.0000). |  |
| building_permits | street_address | direct_identifier | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (PUB-U1 1.0000, PUB-U2 1.0000, PUB-U3 1.0000). |  |
| building_permits | postcode | quasi_identifier | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (PUB-U1 1.0000, PUB-U2 1.0000, PUB-U3 1.0000). |  |
| building_permits | municipality | quasi_identifier | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (PUB-U1 1.0000, PUB-U2 1.0000, PUB-U3 1.0000). |  |
| building_permits | lat | quasi_identifier | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (PUB-U1 1.0000, PUB-U2 1.0000, PUB-U3 1.0000). |  |
| building_permits | lon | quasi_identifier | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (PUB-U1 1.0000, PUB-U2 1.0000, PUB-U3 1.0000). |  |
| building_permits | project_type | non_sensitive | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (PUB-U1 1.0000, PUB-U2 1.0000, PUB-U3 1.0000). |  |
| building_permits | floor_area_m2 | non_sensitive | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (PUB-U1 1.0000, PUB-U2 1.0000, PUB-U3 1.0000). |  |
| building_permits | cost_estimate_eur | non_sensitive | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (PUB-U1 1.0000, PUB-U2 1.0000, PUB-U3 1.0000). |  |
| building_permits | decision | non_sensitive | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (PUB-U1 1.0000, PUB-U2 1.0000, PUB-U3 1.0000). |  |
| building_permits | decision_date | quasi_identifier | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (PUB-U1 1.0000, PUB-U2 1.0000, PUB-U3 1.0000). |  |
| building_permits | case_officer | direct_identifier | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (PUB-U1 1.0000, PUB-U2 1.0000, PUB-U3 1.0000). |  |
| service_requests | request_id | record_key | drop |  | Detected record_key (RECORD_ID). Candidates tried, most private first: drop: within 0.05 (PUB-U1 1.0000, PUB-U2 0.9944, PUB-U3 0.9608). Chosen: drop. |  |
| service_requests | ts_created | quasi_identifier | month |  | Reviewer edit of the selector's contract: month of creation: PUB-U1 counts by month, and the month is in the organisers' suggested k key (postcode, category, month, language). |  |
| service_requests | channel | non_sensitive | drop |  | Detected non_sensitive (CATEGORY). Candidates tried, most private first: drop: within 0.05 (PUB-U1 1.0000, PUB-U2 0.9944, PUB-U3 0.9608). Chosen: drop. |  |
| service_requests | category | non_sensitive | keep |  | Detected non_sensitive (CATEGORY). Candidates tried, most private first: drop: outside 0.05 (PUB-U1 0.0000, PUB-U2 0.0000, PUB-U3 0.9608); kept: within 0.05 (PUB-U1 1.0000, PUB-U2 0.9944, PUB-U3 0.9608). Chosen: kept. | named rule wins over detected role non_sensitive |
| service_requests | language | quasi_identifier | keep |  | Reviewer edit of the selector's contract: kept: the purpose asks whether response times differ between languages, and language is in the suggested k key. | named rule wins over detected role quasi_identifier |
| service_requests | description | free_text | drop |  | Detected free_text (FREE_TEXT). The only candidate for this type is drop. |  |
| service_requests | reporter_name | direct_identifier | drop |  | Detected direct_identifier (PERSON_NAME). The only candidate for this type is drop. |  |
| service_requests | reporter_phone | direct_identifier | drop |  | Detected direct_identifier (PHONE). The only candidate for this type is drop. |  |
| service_requests | reporter_email | direct_identifier | drop |  | Detected direct_identifier (EMAIL). The only candidate for this type is drop. |  |
| service_requests | reporter_account_id | technical_identifier | drop |  | Detected technical_identifier (RECORD_ID). Candidates tried, most private first: drop: within 0.05 (PUB-U1 1.0000, PUB-U2 0.9944, PUB-U3 0.9608). Chosen: drop. |  |
| service_requests | street_address | direct_identifier | drop |  | Detected direct_identifier (STREET_ADDRESS). The only candidate for this type is drop. |  |
| service_requests | postcode | quasi_identifier | prefix | {'n': 3} | Reviewer edit of the selector's contract: 3-digit postcode area, the area unit of PUB-U1 and of the suggested k key. |  |
| service_requests | municipality | quasi_identifier | drop |  | Detected quasi_identifier (MUNICIPALITY). Candidates tried, most private first: drop: within 0.05 (PUB-U1 1.0000, PUB-U2 0.9849, PUB-U3 1.0000). Chosen: drop. |  |
| service_requests | lat | quasi_identifier | round_decimals | {'decimals': 2} | Reviewer edit of the selector's contract: 2-decimal grid (about 1 km), the cell size of PUB-U3's hotspot map. |  |
| service_requests | lon | quasi_identifier | round_decimals | {'decimals': 2} | Reviewer edit of the selector's contract: 2-decimal grid (about 1 km), the cell size of PUB-U3's hotspot map. |  |
| service_requests | handler_name | direct_identifier | drop |  | Detected direct_identifier (PERSON_NAME). The only candidate for this type is drop. |  |
| service_requests | status | non_sensitive | drop |  | Detected non_sensitive (CATEGORY). Candidates tried, most private first: drop: within 0.05 (PUB-U1 1.0000, PUB-U2 0.9944, PUB-U3 0.9608). Chosen: drop. |  |
| service_requests | ts_closed | quasi_identifier | duration | {'since': 'ts_created', 'unit': 'hours', 'as': 'resolution_hours'} | Reviewer edit of the selector's contract: the closing time becomes the hours from creation to closing (resolution_hours, a name the organisers' PUB-U2 reads). PUB-U2 needs the interval, not the calendar; two coarse timestamps cannot give it and two exact ones are a quasi-identifier pair. |  |
| service_requests | response_text | free_text | drop |  | Detected free_text (FREE_TEXT). The only candidate for this type is drop. |  |
| service_requests | language |  | repair:language:set | {'op': 'set', 'value': 'other'} | At-risk rows only: language becomes other. | 28721 rows (only rows in groups with k<5 or l<1) |
| service_requests | lat |  | repair:lat:round | {'op': 'round', 'decimals': 1} | At-risk rows only: coordinate grid made 10 times coarser. | 28216 rows (only rows in groups with k<5 or l<1) |
| service_requests | lon |  | repair:lon:round | {'op': 'round', 'decimals': 1} | At-risk rows only: coordinate grid made 10 times coarser. | 23175 rows (only rows in groups with k<5 or l<1) |
| service_requests | postcode |  | repair:postcode:prefix | {'op': 'prefix', 'n': 2} | At-risk rows only: one postcode digit fewer. | 7932 rows (only rows in groups with k<5 or l<1) |
| service_requests | ts_created, postcode, category, language, lat, lon |  | repair:suppress |  | Rows still at risk after the ladder: every k column suppressed. | 5219 rows (only rows in groups with k<5 or l<1) |
| service_requests | (row) |  | repair:drop_rows |  | Rows still at risk after suppression are not released. | 0 rows (only rows in groups with k<5 or l<1) |
