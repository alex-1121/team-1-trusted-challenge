| table | column | role | pet | params | reason | note |
|---|---|---|---|---|---|---|
| absences | absence_id | record_key | drop |  | Detected record_key (RECORD_ID). Candidates tried, most private first: drop: within 0.05 (EDU-U2 0.9926, EDU-U4 1.0000). Chosen: drop. |  |
| absences | student_id | technical_identifier | token | {'prefix': 'T'} | Detected technical_identifier (RECORD_ID). Candidates tried, most private first: drop: outside 0.05 (EDU-U2 0.6261, EDU-U4 0.0000); keyed token: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: keyed token. A keyed HMAC-SHA256 token keeps joins and carries no order, which a sequential id would give back. |  |
| absences | academic_year | non_sensitive | drop |  | Detected non_sensitive (CATEGORY). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| absences | term | non_sensitive | drop |  | Detected non_sensitive (CATEGORY). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| absences | excused_hours | sensitive_attribute | drop |  | Detected sensitive_attribute (OTHER). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| absences | unexcused_hours | sensitive_attribute | keep |  | Detected sensitive_attribute (OTHER). Candidates tried, most private first: drop: outside 0.05 (EDU-U2 0.6300, EDU-U4 0.0000); kept: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: kept. | named rule wins over detected role sensitive_attribute |
| absences | late_arrivals | sensitive_attribute | keep |  | Detected sensitive_attribute (OTHER). Candidates tried, most private first: drop: outside 0.05 (EDU-U2 0.7518, EDU-U4 1.0000); kept: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: kept. | named rule wins over detected role sensitive_attribute |
| absences | school_code | non_sensitive | drop |  | Detected non_sensitive (CATEGORY). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| counsellor_notes | note_id | record_key | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (EDU-U2 1.0000, EDU-U4 1.0000). |  |
| counsellor_notes | student_id | technical_identifier | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (EDU-U2 1.0000, EDU-U4 1.0000). |  |
| counsellor_notes | note_date | quasi_identifier | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (EDU-U2 1.0000, EDU-U4 1.0000). |  |
| counsellor_notes | author_name | direct_identifier | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (EDU-U2 1.0000, EDU-U4 1.0000). |  |
| counsellor_notes | author_role | quasi_identifier | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (EDU-U2 1.0000, EDU-U4 1.0000). |  |
| counsellor_notes | language | quasi_identifier | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (EDU-U2 1.0000, EDU-U4 1.0000). |  |
| counsellor_notes | note_text | free_text | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (EDU-U2 1.0000, EDU-U4 1.0000). |  |
| course_grades | grade_id | record_key | drop |  | Detected record_key (RECORD_ID). Candidates tried, most private first: drop: within 0.05 (EDU-U2 0.9926, EDU-U4 1.0000). Chosen: drop. |  |
| course_grades | student_id | technical_identifier | token | {'prefix': 'T'} | Detected technical_identifier (RECORD_ID). Candidates tried, most private first: drop: outside 0.05 (EDU-U2 0.9860, EDU-U4 0.0000); keyed token: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: keyed token. A keyed HMAC-SHA256 token keeps joins and carries no order, which a sequential id would give back. |  |
| course_grades | school_code | non_sensitive | drop |  | Detected non_sensitive (CATEGORY). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| course_grades | academic_year | non_sensitive | drop |  | Detected non_sensitive (CATEGORY). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| course_grades | period | sensitive_attribute | drop |  | Detected sensitive_attribute (OTHER). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| course_grades | course_code | non_sensitive | drop |  | Detected non_sensitive (CATEGORY). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| course_grades | course_name | free_text | drop |  | Detected free_text (FREE_TEXT). The only candidate for this type is drop. |  |
| course_grades | credits | sensitive_attribute | drop |  | Detected sensitive_attribute (OTHER). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| course_grades | grade | sensitive_attribute | keep |  | Detected sensitive_attribute (OTHER). Candidates tried, most private first: drop: outside 0.05 (EDU-U2 0.9834, EDU-U4 0.0000); kept: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: kept. | named rule wins over detected role sensitive_attribute |
| course_grades | grade_scale | non_sensitive | keep |  | Detected non_sensitive (CATEGORY). Candidates tried, most private first: drop: outside 0.05 (EDU-U2 1.0000, EDU-U4 0.5322); kept: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: kept. | named rule wins over detected role non_sensitive |
| course_grades | assessed_date | quasi_identifier | drop |  | Detected quasi_identifier (DATE). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| course_grades | teacher_name | direct_identifier | drop |  | Detected direct_identifier (PERSON_NAME). The only candidate for this type is drop. |  |
| matriculation_results | exam_result_id | record_key | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (EDU-U2 1.0000, EDU-U4 1.0000). |  |
| matriculation_results | student_id | technical_identifier | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (EDU-U2 1.0000, EDU-U4 1.0000). |  |
| matriculation_results | exam_session | non_sensitive | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (EDU-U2 1.0000, EDU-U4 1.0000). |  |
| matriculation_results | subject_code | quasi_identifier | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (EDU-U2 1.0000, EDU-U4 1.0000). |  |
| matriculation_results | subject_name | non_sensitive | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (EDU-U2 1.0000, EDU-U4 1.0000). |  |
| matriculation_results | raw_points | sensitive_attribute | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (EDU-U2 1.0000, EDU-U4 1.0000). |  |
| matriculation_results | max_points | non_sensitive | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (EDU-U2 1.0000, EDU-U4 1.0000). |  |
| matriculation_results | grade | non_sensitive | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (EDU-U2 1.0000, EDU-U4 1.0000). |  |
| matriculation_results | grade_points | sensitive_attribute | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (EDU-U2 1.0000, EDU-U4 1.0000). |  |
| matriculation_results | exam_language | quasi_identifier | withhold |  | Withheld: without it every required task stays within 0.05 of the reference (EDU-U2 1.0000, EDU-U4 1.0000). |  |
| students | student_id | record_key | token | {'prefix': 'T'} | Detected record_key (RECORD_ID). Candidates tried, most private first: drop: outside 0.05 (EDU-U2 0.0000, EDU-U4 1.0000); keyed token: within 0.05 (EDU-U2 0.9926, EDU-U4 1.0000). Chosen: keyed token. A keyed HMAC-SHA256 token keeps joins and carries no order, which a sequential id would give back. |  |
| students | learner_id | direct_identifier | drop |  | Detected direct_identifier (STUDENT_ID). The only candidate for this type is drop. |  |
| students | hetu | direct_identifier | drop |  | Detected direct_identifier (NATIONAL_ID). The only candidate for this type is drop. |  |
| students | first_names | direct_identifier | drop |  | Detected direct_identifier (PERSON_NAME). The only candidate for this type is drop. |  |
| students | last_name | direct_identifier | drop |  | Detected direct_identifier (PERSON_NAME). The only candidate for this type is drop. |  |
| students | birth_date | quasi_identifier | drop |  | Detected quasi_identifier (BIRTH_DATE). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| students | sex | quasi_identifier | drop |  | Detected quasi_identifier (SEX). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| students | home_language | quasi_identifier | drop |  | Detected quasi_identifier (LANGUAGE). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| students | street_address | direct_identifier | drop |  | Detected direct_identifier (STREET_ADDRESS). The only candidate for this type is drop. |  |
| students | postcode | quasi_identifier | drop |  | Detected quasi_identifier (POSTCODE). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| students | municipality | quasi_identifier | drop |  | Detected quasi_identifier (MUNICIPALITY). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| students | guardian1_name | direct_identifier | drop |  | Detected direct_identifier (PERSON_NAME). The only candidate for this type is drop. |  |
| students | guardian1_phone | direct_identifier | drop |  | Detected direct_identifier (PHONE). The only candidate for this type is drop. |  |
| students | guardian2_name | direct_identifier | drop |  | Detected direct_identifier (PERSON_NAME). The only candidate for this type is drop. |  |
| students | guardian2_phone | direct_identifier | drop |  | Detected direct_identifier (PHONE). The only candidate for this type is drop. |  |
| students | school_code | non_sensitive | drop |  | Detected non_sensitive (CATEGORY). Candidates tried, most private first: drop: within 0.05 (EDU-U2 0.9975, EDU-U4 1.0000). Chosen: drop. |  |
| students | school_name | quasi_identifier | drop |  | Detected quasi_identifier (ORG_NAME). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| students | programme | non_sensitive | drop |  | Detected non_sensitive (CATEGORY). Candidates tried, most private first: drop: within 0.05 (EDU-U2 0.9964, EDU-U4 1.0000). Chosen: drop. |  |
| students | class_group | technical_identifier | drop |  | Detected technical_identifier (RECORD_ID). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| students | start_date | quasi_identifier | drop |  | Detected quasi_identifier (DATE). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| students | special_support | non_sensitive | drop |  | Detected non_sensitive (CATEGORY). Candidates tried, most private first: drop: within 0.05 (EDU-U2 0.9926, EDU-U4 1.0000). Chosen: drop. |  |
| students | finnish_as_second_language | sensitive_attribute | drop |  | Detected sensitive_attribute (OTHER). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
| students | status | non_sensitive | keep |  | Detected non_sensitive (CATEGORY). Candidates tried, most private first: drop: outside 0.05 (EDU-U2 0.0000, EDU-U4 1.0000); kept: within 0.05 (EDU-U2 0.9926, EDU-U4 1.0000). Chosen: kept. | named rule wins over detected role non_sensitive |
| students | end_date | quasi_identifier | drop |  | Detected quasi_identifier (DATE). Candidates tried, most private first: drop: within 0.05 (EDU-U2 1.0000, EDU-U4 1.0000). Chosen: drop. |  |
