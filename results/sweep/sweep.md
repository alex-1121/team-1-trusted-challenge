# HEALTH-S1 sweep

Every number is copied from the cell's scorecard.json, except own k<5 and seconds, which `sweep` computes and times. self-assessment, not the official judging score.

| cell (age width, hour block) | H-U2 | H-U4 | H-U6 | H-U7 | H-U8 | scorer k<5 | own k<5 | privacy | utility | composite | seconds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| w5_b1 (5, 1) | 1.0 | 1.0 | 0.9641950063457823 | 1.0 | 1.0 | 0.301 | 0.1683 | 0.8194 | 0.9928 | 0.8901 | 7.8 |
| w5_b2 (5, 2) | 1.0 | 1.0 | 0.9641950063457823 | 1.0 | 0.0 | 0.1662 | 0.0739 | 0.9003 | 0.7928 | 0.848 | 7.6 |
| w5_b3 (5, 3) | 1.0 | 1.0 | 0.9641950063457823 | 1.0 | 0.0 | 0.1082 | 0.0374 | 0.9351 | 0.7928 | 0.8646 | 7.6 |
| w10_b1 (10, 1) | 1.0 | 1.0 | 0.9641950063457823 | 1.0 | 1.0 | 0.1817 | 0.0779 | 0.891 | 0.9928 | 0.9346 | 7.6 |
| w10_b2 (10, 2) | 1.0 | 1.0 | 0.9641950063457823 | 1.0 | 0.0 | 0.0854 | 0.0228 | 0.9488 | 0.7928 | 0.8709 | 7.6 |
| w10_b3 (10, 3) | 1.0 | 1.0 | 0.9641950063457823 | 1.0 | 0.0 | 0.0525 | 0.0096 | 0.9685 | 0.7928 | 0.8799 | 7.8 |
| w20_b1 (20, 1) | 1.0 | 1.0 | 0.02710592756380137 | 1.0 | 1.0 | 0.0992 | 0.0273 | 0.9405 | 0.8054 | 0.8739 | 7.8 |
| w20_b2 (20, 2) | 1.0 | 1.0 | 0.02710592756380137 | 1.0 | 0.0 | 0.0416 | 0.0075 | 0.975 | 0.6054 | 0.7632 | 7.8 |
| w20_b3 (20, 3) | 1.0 | 1.0 | 0.02710592756380137 | 1.0 | 0.0 | 0.0239 | 0.0033 | 0.9857 | 0.6054 | 0.7668 | 7.8 |

Total runtime: 69 seconds.

## Rule

Keep the cells where every required task scores at least 0.9. Among them, if any cell has own k<5 share at or below 0.05, take the best composite among those cells. Otherwise take the lowest own k<5 share among the eligible cells that tie on the best composite (composites compared at 4 decimals). If no cell clears the floor, the same two steps run over all cells.

Required tasks: H-U2, H-U4, H-U6, H-U7, H-U8. Own k columns: date_of_birth, sex, municipality, arrival_ts.

## Chosen cell

w10_b1: age band width 10 years, arrival hour block 1 hours (composite 0.9346, own k<5 0.0779). The contract is not edited here; the deliverables ticket adopts these parameters.
