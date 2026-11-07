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

## EDU-S2 after MIN_GAIN

Rule added 2026-11-07: a candidate other than drop competes only if it raises at least one required task by MIN_GAIN 0.01 over drop (per task). Same select command, written as `<scenario>.v3.json`. HEALTH-S1 v3 (wall time 201.1 s): 38 of 38 entries identical to the shipped contract on pet and params, k target equal, no move after repair; only the reasons changed, so `contracts/HEALTH-S1.json`, `contracts/generated/HEALTH-S1.v2.json` and `results/selection/HEALTH-S1.v2.json` were replaced by the v3 run.

| Item | EDU-S2 v2 | EDU-S2 v3 (MIN_GAIN) | v1 (`contracts/generated/EDU-S2.auto.json`) |
| --- | --- | --- | --- |
| Wall time | 92.4 s | 133.5 s | - |
| students.special_support | keep | drop (gain over drop: EDU-U2 0.0038, under 0.01) | drop |
| students.school_code | keep | drop (gain over drop: EDU-U2 0.0025, under 0.01) | drop |
| Differences vs v1 (pet and params, 44 column entries) | 2 | 0 | - |
| Post-repair risk, students | 0.0124 | 0.0000 | - |
| Post-repair risk, absences / course_grades | 0.0000 / 0.0000 | 0.0000 / 0.0000 | - |
| Fitness (share in a group under 5): absences, course_grades, students | 0.0369, 0.0001, 0.0124 | 0.0369, 0.0001, 0.0000 | - |
| Final EDU-U2, EDU-U4 after repair | 1.0000, 1.0000 | 0.9926, 1.0000 | - |
