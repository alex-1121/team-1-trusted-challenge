# Selector v2 comparison (task 4)

Plain results of running the v2 contract and the v2 selector. Every number comes from a run on 2026-11-07.

## Commands

- Build (all outputs under a scratch folder, not in the repo):
  `.venv/bin/python -m pets_transformer.cli build --scenario HEALTH-S1 --contract contracts/generated/HEALTH-S1.v2.json --out <scratch>/out --results <scratch>/results --submission <scratch>/sub`
- Select: `.venv/bin/python -m pets_transformer.cli select --scenario <HEALTH-S3|EDU-S2> --out <scratch>/<scenario>.v2.json --evidence <scratch>/<scenario>.evidence.json`

## HEALTH-S1 v2 build (wall time 56.4 s)

- Redteam gate: pass. Every attack at or below its threshold.
- Required-task floor (0.5): pass.
- Regex scan for direct identifiers: none found.
- Informed attacker, joined-table k and l-diversity checks ran; l-diversity finding: false.
- Residual risk: no risk component above zero.

| Item | v2 build | Shipped build | Difference |
| --- | --- | --- | --- |
| privacy | 1.0 | 1.0 | 0 |
| utility | 0.971 | 0.971 | 0 |
| composite | 0.9866 | 0.9866 | 0 |
| H-U2 | 0.9979 | 0.9979 | 0 |
| H-U4 | 0.9549 | 0.9549 | 0 |
| H-U6 | 0.9578 | 0.9578 | 0 |
| H-U7 | 1.0000 | 1.0000 | 0 |
| H-U8 | 0.9446 | 0.9446 | 0 |

No difference beyond 0.001.

## Generality (v2 select against the v1 contracts in contracts/generated)

Compared pet and params per column, plus the table action. Reasons differ and are ignored.

| Scenario | Wall time | Result vs v1 | Post-repair risk | Fitness block (share of rows in a group under 5) |
| --- | --- | --- | --- | --- |
| HEALTH-S3 | 172.5 s | identical (33 entries) | ed_visits 0.0001 | ed_visits 0.9976 |
| EDU-S2 | 92.4 s | 2 changes (49 entries) | absences 0.0000, course_grades 0.0000, students 0.0124 | absences 0.0369, course_grades 0.0001, students 0.0124 |

EDU-S2 changes (v1 -> v2):
- students.school_code: drop -> keep
- students.special_support: drop -> keep

Final task scores after repair: HEALTH-S3 H-U2, H-U3, H-U5 all 1.0000; EDU-S2 EDU-U2, EDU-U4 both 1.0000.
