# Training the type model's head

The runbook for Task 6 of `plans/2026-11-07-eu-column-types-implementation.md`. The model is a frozen multilingual sentence encoder (`intfloat/multilingual-e5-small`, MIT licence) plus a small classifier head (`head.npz` + `meta.json`, under 2 MB) that is committed. Only the head is trained.

Only fake data is used. The training corpus is made by `gen_corpus.py` from Faker and the committed word lists in `llm_values/`. `train.py` refuses any input that is not such a corpus, and any path under `data/proving-ground`.

Where it runs: zray's laptop (`--device cpu`), because step 2 measured it fast enough (a full run takes about 17 minutes of encoding, once). A teammate's M5 MacBook (`--device mps`, steps 3 to 6) and a cloud GPU (step 7) are the fallbacks.

## 1. Pin the encoder (zray, once)

```bash
.venv/bin/python -c "from huggingface_hub import HfApi; print(HfApi().model_info('intfloat/multilingual-e5-small').sha)"
```

Check that the model card says MIT. The pinned revision is `REVISION` below and goes into `meta.json`.

Pinned (2026-11-07, model card licence: MIT):

```bash
REVISION=614241f622f53c4eeff9890bdc4f31cfecc418b3
```

## 2. Timing run on zray's laptop

```bash
.venv/bin/python scripts/semantic/gen_corpus.py --out /tmp/corpus10 --per-type 10 --seed 1000
.venv/bin/python scripts/semantic/train.py --corpus /tmp/corpus10 --out /tmp/models10 --revision $REVISION --device cpu
```

It prints values per second while encoding. The full corpus has about 224,000 distinct values; divide to get the laptop's time for a full run.

Measured 2026-11-07 on zray's laptop (12 CPU threads, CPU-only torch): 218 values per second, 3 min 49 s wall clock for the small corpus (46,833 values), 1.5 GB peak memory. So the full corpus takes about 17 minutes, and the full run goes on the laptop:

```bash
.venv/bin/python scripts/semantic/train.py --corpus data/semantic-corpus --out out/models --revision $REVISION --device cpu
```

Then copy the files as in step 6 (`out/models/` instead of the teammate's files) and skip steps 3 to 5.

## 3. Set up the M5 MacBook (teammate)

Needs Python 3.10 or newer and read access to the private fork `zraycd/team-1-trusted`.

```bash
git clone https://github.com/zraycd/team-1-trusted.git -b feat/semantic-types
cd team-1-trusted
python3 -m venv v
v/bin/pip install -e '.[semantic,train]'
v/bin/python -m pets_transformer.semantic.model --download --encoder intfloat/multilingual-e5-small --revision $REVISION
```

## 4. Make the corpus and check its hashes (teammate)

```bash
v/bin/python scripts/semantic/gen_corpus.py --out data/semantic-corpus --per-type 60 --seed 1000
```

The three printed SHA-256 hashes must equal these (also in `results/detect-semantic/corpus.json`):

- train `397221a591c2f9946e4059e1b2af10b191845de4c4c44467bb02e4b0e278adae`
- calib `c8bccca72c4ea10c1b8a89b3d8956a11da4a7237089d2fdd7b5116284ccc6654`
- locked `68ed961b91d6cd3aa8c3320ec6e57aa6ec6ae4ad4aa6d03c3a1dd426eaa060d4`

On a mismatch, stop and tell zray: the Faker version (`v/bin/pip show faker` must say 40.44.0) or the word lists differ.

## 5. Train (teammate)

```bash
v/bin/python scripts/semantic/train.py --corpus data/semantic-corpus --out out/models --revision $REVISION --device mps
```

It encodes every distinct value once (cached in `data/semantic-corpus/.emb/`, so a second run skips this), fits the head on `train.jsonl`, fits the temperature on `calib.jsonl` (Slovak, Romanian and Greek, never seen in training) and prints accuracy, macro-F1 and ECE (expected calibration error) on `calib`. `locked.jsonl` is not read.

If `mps` fails, run the same command with `--device cpu`.

## 6. Send back three files (teammate)

`out/models/head.npz`, `out/models/meta.json` and `out/models/train_report.json`, by AirDrop or chat. Nothing else comes back, and nothing of zray's goes to the MacBook: no copy of `data/proving-ground/`, `data/semantic-eval/`, `results/` or zray's `out/`.

zray then copies `head.npz` and `meta.json` to `src/pets_transformer/semantic/models/`, `train_report.json` to `results/detect-semantic/`, and checks that `meta.json`'s `trained_on.sha256` equals `corpus.json`.

## 7. Fallbacks

1. The same commands on zray's laptop with `--device cpu`.
2. A cloud GPU (Vultr or Google Cloud). Create the machine in the web console. Copy only `pyproject.toml`, `src/pets_transformer/`, `scripts/semantic/` and `data/semantic-corpus/`. Destroy the machine when done, check in the console that it is gone, and note the cost.
