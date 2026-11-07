# Detector results on the held-out datasets

Split and protocol: `SPLIT.md`. Two rules were added after the first run (see "Before and after the two added rules" below); the held-out numbers did not change. Eight more rules came with issue #23 (see "Issue #23" below); the committed JSON is the #23 run. Numbers are copied from the `pets-eval detect` JSON next to this file (`<dataset>.json`). Target: macro-F1 above 0.65 (organiser rule baseline B1).

## Issue #23 rules: before and after

Before = the #15 run, after = the #23 run, both from `pets-eval detect --datasets <dataset>`. The #23 rules were written after reading public_admin's error list and the held-out catalog rows (`SPLIT.md`), so the after numbers are not a clean held-out result.

| Dataset | macro-F1 before | macro-F1 after | accuracy before | accuracy after | sensitive_recall before | sensitive_recall after | subtype_accuracy before | subtype_accuracy after | target met after |
|---|---|---|---|---|---|---|---|---|---|
| health | 0.8086 | 0.8086 | 0.717 | 0.717 | 0.7209 | 0.7209 | 0.6226 | 0.6226 | yes |
| public_admin | 0.5431 | 0.7241 | 0.7568 | 0.8108 | 0.8519 | 0.8519 | 0.8378 | 0.8919 | yes |
| customer_service | 0.7462 | 0.7821 | 0.7436 | 0.7692 | 0.9565 | 0.9565 | 0.6667 | 0.6923 | yes |

What changed on the held-out sets: only the record-key rule fired. public_admin `service_requests.request_id` and `building_permits.permit_id` moved from technical_identifier HOSTNAME to record_key RECORD_ID (record_key F1 0.0 to 1.0, technical_identifier F1 0.4 to 0.6667). customer_service `conversations.conversation_id` moved from direct_identifier EMPLOYEE_ID to record_key RECORD_ID (record_key F1 0.8 to 1.0). No held-out number dropped. No health label changed. The six tuning datasets were re-run and scored; none of their labels changed.

public_admin's one sensitive attribute (`cost_estimate_eur`, whole euros such as `14500`) is still non_sensitive: the monthly-pay rule needs two-decimal amounts and was not widened to fit it.

### Unseen columns whose label changed

| Column | Value shape | Old label | New label |
|---|---|---|---|
| c02 | `KC-4450`, 700 distinct values over 2818 rows, points at no other table | technical_identifier RECORD_ID | direct_identifier EMPLOYEE_ID |
| c11 | amounts like `3 987,96`, 5th to 95th percentile about 1892 to 4421 | quasi_identifier FINANCIAL_DATA | sensitive_attribute FINANCIAL_DATA |
| c13 | 3-value code (`AY-HL`, `AY-PS`, `AY-TK`), blank on 23 % of rows | non_sensitive CATEGORY | sensitive_attribute CATEGORY |
| c14 | amounts like `28.04`, `0.00` on exactly the rows where c13 is blank | quasi_identifier FINANCIAL_DATA | sensitive_attribute FINANCIAL_DATA |
| c20 | 64-hex hash, 700 distinct values, one-to-one with c02 | non_sensitive OTHER | technical_identifier OTHER |
| c22 | Finnish care titles (`lähihoitaja`, `sairaanhoitaja`, `osastonhoitaja`, ...) | non_sensitive CATEGORY | quasi_identifier OCCUPATION |

c05 (HETU, 25 % with a `HETU ` prefix) was already direct_identifier NATIONAL_ID; the prefix rule makes that hold when most values carry the prefix. The phone rule changes no column in any dataset here.

## #15 run (before issue #23)

| Dataset | macro-F1 | accuracy | sensitive_recall | subtype_accuracy | fields | target met |
|---|---|---|---|---|---|---|
| health | 0.8086 | 0.717 | 0.7209 | 0.6226 | 53 | yes |
| public_admin | 0.5431 | 0.7568 | 0.8519 | 0.8378 | 37 | no |
| customer_service | 0.7462 | 0.7436 | 0.9565 | 0.6667 | 39 | yes |

## F1 per role, #15 run (support in brackets)

| Role | health | public_admin | customer_service |
|---|---|---|---|
| direct_identifier | 1.0 (6) | 0.8889 (9) | 0.8235 (9) |
| quasi_identifier | 0.8148 (15) | 0.8462 (13) | 0.9333 (7) |
| sensitive_attribute | 0.5217 (16) | 0.0 (1) | 0.25 (2) |
| technical_identifier | 0.8889 (4) | 0.4 (2) | 0.75 (3) |
| free_text | 1.0 (2) | 1.0 (2) | 1.0 (2) |
| record_key | 1.0 (4) | 0.0 (2) | 0.8 (3) |
| non_sensitive | 0.4348 (6) | 0.6667 (8) | 0.6667 (13) |

## Errors in the #15 run (catalog rows read after the run)

- health: 9 sensitive attributes labelled non_sensitive, 3 quasi-identifiers labelled non_sensitive. Sensitive values that look like ordinary categories or numbers are the main miss.
- public_admin (target missed): both record keys (`service_requests.request_id`, `building_permits.permit_id`) labelled technical_identifier, so record_key F1 is 0.0 and its one sensitive attribute (`cost_estimate_eur`) is labelled non_sensitive, so sensitive_attribute F1 is 0.0. With only 1 and 2 supporting columns, these two roles pull macro-F1 under 0.65 while accuracy is 0.7568. Other misses: `property_id` (direct_identifier) and `applicant_business_id` (technical_identifier) labelled non_sensitive, `municipality` labelled quasi_identifier where the catalog says non_sensitive (twice), `street_address` labelled direct_identifier where the catalog says quasi_identifier, `floor_area_m2` labelled non_sensitive.
- customer_service: 5 non_sensitive columns labelled sensitive_attribute, 2 direct identifiers labelled technical_identifier.

## Before and after the two added rules

The HETU-without-century-sign rule and the one-field address rule (`SPLIT.md`) were added after inspecting unseen export values. Every held-out dataset was re-scored with `pets-eval detect`. No held-out label changed, so the numbers are identical. (The committed JSON is now the #23 run.)

| Dataset | macro-F1 before | macro-F1 after | sensitive_recall before | sensitive_recall after |
|---|---|---|---|---|
| health | 0.8086 | 0.8086 | 0.7209 | 0.7209 |
| public_admin | 0.5431 | 0.5431 | 0.8519 | 0.8519 |
| customer_service | 0.7462 | 0.7462 | 0.9565 | 0.9565 |

The six tuning datasets were re-run too; none of their labels changed.

## Unseen HR export

`unseen_field_labels.csv` (format `column,privacy_role,subtype`, 26 rows) comes from the #23 run (changes in the table above). It has no labels to score against here; the organisers hold them. The two added rules changed c05 (non_sensitive CATEGORY to direct_identifier NATIONAL_ID) and c07 (free_text FREE_TEXT to direct_identifier STREET_ADDRESS).
