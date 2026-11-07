# Red-team gate results

Attacks the organisers' scorecard does not run, each with a threshold (`src/pets_transformer/redteam.py`). JSON files hold counts and rates only.

| Attack | What it measures | Threshold |
|---|---|---|
| order_attack | share of rows whose dropped date is rebuilt from the file order, a sequential key, or the first row per key in a linked table | at most 0.05 |
| news_linkage | share of the shipped news clips that single out the right patient, using the rebuilt dates | 0 |
| person_fingerprint | share of persons (pseudonym, or a token that repeats within a table) unique by their quasi-identifiers and their set of arrival hours | at most 0.05 |
| scorer_linkage_band_aware | the organisers' own linkage attacker (`pets_eval.attacks.linkage_attack`, `metadata/attack_specs.json`) rerun with the age read from the age band and the unmatchable hour-only time left out | at most 0.01 |
| plain_hash | share of a released column's values that equal the MD5, SHA-1 or SHA-256 of an original value | 0 |

Every build also checks utility: every required task must score at least 0.5, or the release is refused as useless.

- `before-7cf541b.json`: the release built by main's own code at commit 7cf541b. Gate: fail.
  Command: `python -m pets_transformer.cli redteam --protected <release of 7cf541b> --original data/proving-ground/data/health --contract <contracts/HEALTH-S1.json at 7cf541b> --truth data/proving-ground/truth --adversary data/proving-ground/adversary --attack-specs data/proving-ground/metadata/attack_specs.json --out results/redteam/before-7cf541b.json`
- Each build writes its own `results/<scenario>-build/redteam.json`.
