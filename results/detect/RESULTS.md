# Detector results on the held-out datasets

Split and protocol: `SPLIT.md`. Two rules were added after the first run (see "Before and after the two added rules" below); the held-out numbers did not change. Numbers are copied from the `pets-eval detect` JSON next to this file (`<dataset>.json`). Target: macro-F1 above 0.65 (organiser rule baseline B1).

| Dataset | macro-F1 | accuracy | sensitive_recall | subtype_accuracy | fields | target met |
|---|---|---|---|---|---|---|
| health | 0.8086 | 0.717 | 0.7209 | 0.6226 | 53 | yes |
| public_admin | 0.5431 | 0.7568 | 0.8519 | 0.8378 | 37 | no |
| customer_service | 0.7462 | 0.7436 | 0.9565 | 0.6667 | 39 | yes |

## F1 per role (support in brackets)

| Role | health | public_admin | customer_service |
|---|---|---|---|
| direct_identifier | 1.0 (6) | 0.8889 (9) | 0.8235 (9) |
| quasi_identifier | 0.8148 (15) | 0.8462 (13) | 0.9333 (7) |
| sensitive_attribute | 0.5217 (16) | 0.0 (1) | 0.25 (2) |
| technical_identifier | 0.8889 (4) | 0.4 (2) | 0.75 (3) |
| free_text | 1.0 (2) | 1.0 (2) | 1.0 (2) |
| record_key | 1.0 (4) | 0.0 (2) | 0.8 (3) |
| non_sensitive | 0.4348 (6) | 0.6667 (8) | 0.6667 (13) |

## Errors (catalog rows read after the run)

- health: 9 sensitive attributes labelled non_sensitive, 3 quasi-identifiers labelled non_sensitive. Sensitive values that look like ordinary categories or numbers are the main miss.
- public_admin (target missed): both record keys (`service_requests.request_id`, `building_permits.permit_id`) labelled technical_identifier, so record_key F1 is 0.0 and its one sensitive attribute (`cost_estimate_eur`) is labelled non_sensitive, so sensitive_attribute F1 is 0.0. With only 1 and 2 supporting columns, these two roles pull macro-F1 under 0.65 while accuracy is 0.7568. Other misses: `property_id` (direct_identifier) and `applicant_business_id` (technical_identifier) labelled non_sensitive, `municipality` labelled quasi_identifier where the catalog says non_sensitive (twice), `street_address` labelled direct_identifier where the catalog says quasi_identifier, `floor_area_m2` labelled non_sensitive.
- customer_service: 5 non_sensitive columns labelled sensitive_attribute, 2 direct identifiers labelled technical_identifier.

## Before and after the two added rules

The HETU-without-century-sign rule and the one-field address rule (`SPLIT.md`) were added after inspecting unseen export values. Every held-out dataset was re-scored with `pets-eval detect`. No held-out label changed, so the numbers are identical. The committed JSON is the after run.

| Dataset | macro-F1 before | macro-F1 after | sensitive_recall before | sensitive_recall after |
|---|---|---|---|---|
| health | 0.8086 | 0.8086 | 0.7209 | 0.7209 |
| public_admin | 0.5431 | 0.5431 | 0.8519 | 0.8519 |
| customer_service | 0.7462 | 0.7462 | 0.9565 | 0.9565 |

The six tuning datasets were re-run too; none of their labels changed.

## Unseen HR export

`unseen_field_labels.csv` (format `column,privacy_role,subtype`, 26 rows) comes from the after run. It has no labels to score against here; the organisers hold them. The two added rules changed c05 (non_sensitive CATEGORY to direct_identifier NATIONAL_ID) and c07 (free_text FREE_TEXT to direct_identifier STREET_ADDRESS).
