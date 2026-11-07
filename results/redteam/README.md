# Red-team gate results

Attacks the organisers' scorecard does not run, each with a threshold (`src/pets_transformer/redteam.py`). JSON files hold counts and rates only.

- `before-7cf541b.json`: the release built by main's own code at commit 7cf541b. Gate: fail.
  Command: `python -m pets_transformer.cli redteam --protected <release of 7cf541b> --original data/proving-ground/data/health --contract <contracts/HEALTH-S1.json at 7cf541b> --truth data/proving-ground/truth --adversary data/proving-ground/adversary --out results/redteam/before-7cf541b.json`
- `after.json`: written by `python -m pets_transformer.cli build --scenario HEALTH-S1` on the current release. Gate: pass.

Thresholds: order attack at most 0.05 of rows with the date rebuilt; news-clip linkage 0 patients named; person fingerprint at most 0.05 of persons unique. They are our choice and are stated in each JSON.
