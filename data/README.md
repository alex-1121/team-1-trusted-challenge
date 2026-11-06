# Data

`data/proving-ground/` is gitignored. It holds the TrustED PETs Proving Ground 2026 (580 MB unzipped, 261 files, synthetic, CC BY 4.0, (c) 2026 Since AI ry).

To restore it:

1. Get `TRUSTED_SinceAI2026_FINAL.zip` from the organiser materials in sinceai.app or from a teammate who has it (210 MB, not in any repo). Inside it is `TRUSTED_PETS_PROVING_GROUND_2026 (1).zip`.
2. Unzip that inner archive into `data/`. It unpacks into a folder named `TRUSTED_PETS_PROVING_GROUND_2026`; rename that folder to `proving-ground` so that `data/proving-ground/START_HERE.md` exists.
3. Read `START_HERE.md` first. Read every CSV with `dtype=str`.

Rules: `rowmap_*.csv` are never published (organiser rule). `truth/` and `holdout/` stay out of the repo and the submission zip as well (our caution: they are the answer key to the attacks). Attribution for anything we publish: "TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0)".
