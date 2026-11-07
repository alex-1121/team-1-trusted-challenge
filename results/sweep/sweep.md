# HEALTH-S1 sweep

Every number is copied from the cell's scorecard.json, except own k<5 and seconds, which `sweep` computes and times. self-assessment, not the official judging score.

| cell (age width, hour block) | H-U2 | H-U4 | H-U6 | H-U7 | H-U8 | scorer k<5 | own k<5 | privacy | utility | composite | seconds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| w5_b1 (5, 1) | 0.9978835978835979 | 1.0 | 0.9641950063457823 | 1.0 | 0.9985113097635784 | 0.0711 | 0.0711 | 0.9573 | 0.9921 | 0.9728 | 17.5 |
| w5_b2 (5, 2) | 0.9978835978835979 | 1.0 | 0.9641950063457823 | 1.0 | 0.0 | 0.0229 | 0.0229 | 0.9863 | 0.7924 | 0.8876 | 17.4 |
| w5_b3 (5, 3) | 0.9978835978835979 | 1.0 | 0.9641950063457823 | 1.0 | 0.0 | 0.0105 | 0.0105 | 0.9937 | 0.7924 | 0.8908 | 17.4 |
| w10_b1 (10, 1) | 0.9978835978835979 | 1.0 | 0.9641950063457823 | 1.0 | 0.9985113097635784 | 0.0227 | 0.0227 | 0.9864 | 0.9921 | 0.989 | 17.4 |
| w10_b2 (10, 2) | 0.9978835978835979 | 1.0 | 0.9641950063457823 | 1.0 | 0.0 | 0.0059 | 0.0059 | 0.9965 | 0.7924 | 0.8921 | 17.3 |
| w10_b3 (10, 3) | 0.9978835978835979 | 1.0 | 0.9641950063457823 | 1.0 | 0.0 | 0.003 | 0.0030 | 0.9982 | 0.7924 | 0.8928 | 17.4 |
| w20_b1 (20, 1) | 0.9978835978835979 | 1.0 | 0.02710592756380137 | 1.0 | 0.9985113097635784 | 0.0077 | 0.0077 | 0.9954 | 0.8047 | 0.8986 | 17.4 |
| w20_b2 (20, 2) | 0.9978835978835979 | 1.0 | 0.02710592756380137 | 1.0 | 0.0 | 0.0024 | 0.0024 | 0.9986 | 0.605 | 0.7707 | 17.4 |
| w20_b3 (20, 3) | 0.9978835978835979 | 1.0 | 0.02710592756380137 | 1.0 | 0.0 | 0.002 | 0.0020 | 0.9988 | 0.605 | 0.7708 | 17.4 |

Total runtime: 157 seconds.

## Rule

Keep the cells where every required task scores at least 0.9. Among them, if any cell has own k<5 share at or below 0.05, take the best composite among those cells. Otherwise take the lowest own k<5 share among the eligible cells that tie on the best composite (composites compared at 4 decimals). If no cell clears the floor, the same two steps run over all cells.

Required tasks: H-U2, H-U4, H-U6, H-U7, H-U8. Own k columns: date_of_birth, sex, municipality, arrival_ts.

## Chosen cell

w10_b1: age band width 10 years, arrival hour block 1 hours (composite 0.989, own k<5 0.0227). The contract is not edited here; the deliverables ticket adopts these parameters.
