# EU Column Types (word lists first, model for the rest) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

Status: proposed. Author: Claude Opus 5.5, run by zray, 2026-11-07. Comment inline as `> note (name):` lines.

**Goal:** Every text column the word lists cannot place gets a type from a small multilingual model with calibrated probabilities. Disagreements that change a column's treatment print a warning and land in `needs_review.csv`. Nothing after detection changes.

**Architecture:** `detect.classify` keeps its rules and also reports which rule fired. A new package `pets_transformer.semantic` holds four parts: the type list, the decision and combine rules, the shared feature code, and a loader for a frozen sentence encoder plus a small committed classifier head. `detect_dataset_report` runs both and combines them; `detect_dataset` keeps its old signature and returns only the labels. Training-data generation, training and evaluation are scripts under `scripts/semantic/`. Training runs on a teammate's M5 MacBook (zray's laptop as fallback, a cloud GPU as last resort). Only fake data reaches Featherless or any machine other than zray's laptop.

**Tech Stack:** Python 3.10+, pandas, numpy; optional extra `semantic`: sentence-transformers (encoder `intfloat/multilingual-e5-small`, pinned revision); optional extra `train`: scikit-learn, Faker (one exact pinned version, so every machine generates the same corpus), openai (client for Featherless's OpenAI-compatible API); pytest; the organisers' `pets_eval.detect.score_detection`.

**Spec:** `plans/2026-11-07-eu-column-types.md` (approved by zray 2026-11-07). Read it first; this plan argues from it.

## Global Constraints

- Thresholds: confident at top probability >= 0.80; protect anyway for the most protective type at >= 0.20; disagreement warning when the model gives the word list's type < 0.30.
- Encoder: open licence, multilingual, at most 500 MB, runs on CPU. Downloaded once by an explicit command; at run time it loads from the local cache only (`local_files_only=True`), so processing never touches the network.
- No real or proving-ground value is ever sent to Featherless, a teammate's machine, a cloud machine or any hosted model. Only data made by `scripts/semantic/` generators leaves zray's laptop, and the training machine generates its own copy.
- No values in any output file. `type_probs.csv`, `needs_review.csv` and every JSON hold column names, types, probabilities and counts only.
- Values only: the model never reads column headers.
- New dependencies only in optional extras (`semantic`, `train`) in `pyproject.toml`; the base install stays `pandas`.
- Without the `semantic` extra or the cached encoder, the detector falls back to `lexicon` and prints one warning line saying so.
- No model weights in git or the submission zip. The committed head (`head.npz` + `meta.json`) stays under 2 MB.
- Read every CSV with `dtype=str` (AGENTS.md).
- Every published number comes from a committed JSON in `results/detect-semantic/` (AGENTS.md). No em-dash in any written file; use " - ".
- Git: work on branch `feat/semantic-types` pushed to the fork `zraycd/team-1-trusted`. Before every push follow AGENTS.md's Git section. Never force-push `main`. Push only when zray says so.
- Deadline: go or no-go Sunday 08:00 Turku time; submission closes 10:00.

## Review Focus

1. **A column with very few or identical values** (2 non-empty values, or one value repeated): features must not produce NaN, and the model is skipped (the word-list label stands, no warning). Test in Task 2 (`test_degenerate_column_features_are_finite`) and Task 3 (`test_tiny_column_skips_model`).
2. **A sampled value leaking into an output file:** a person's name in `needs_review.csv` would itself be a leak. Test in Task 3 (`test_outputs_hold_no_values`).
3. **Very long free-text values** (clinical notes of several thousand characters): runtime and encoder truncation. Values are cut to 256 characters before encoding. Test in Task 2 (`test_long_values_are_truncated`).
4. **No network, no extra, or no cached encoder:** the build must still run, on word lists, with one warning. Test in Task 2 (`test_unavailable_model_falls_back`) and Task 3 (`test_hybrid_request_without_model_runs_lexicon`).
5. **A proving-ground or other real file handed to the training script by mistake:** `train.py` must refuse any input that is not a corpus written by `gen_corpus.py`. Test in Task 6 (`test_train_refuses_non_corpus_input`).

---

## File map

| Path | Responsibility | Task |
|---|---|---|
| `src/pets_transformer/semantic/__init__.py` | re-exports; `resolve_mode` | 2 |
| `src/pets_transformer/semantic/types.py` | type list, type to (role, subtype), protect rank, word-list rule to type | 1 |
| `src/pets_transformer/semantic/decide.py` | `Decision`, `decide`, `treatment`, `combine` | 1 |
| `src/pets_transformer/semantic/features.py` | `sample_values`, `shape_stats`, `column_vector` (shared by training and run time) | 2 |
| `src/pets_transformer/semantic/model.py` | `TypeModel`, `load_model`, `available`, download command | 2 |
| `src/pets_transformer/semantic/metrics.py` | `ece`, `reliability` | 2 |
| `src/pets_transformer/semantic/models/head.npz`, `meta.json` | the trained head (committed) | 6 |
| `src/pets_transformer/detect.py` | `classify_traced`, `detect_dataset_report`, `--semantic` | 3 |
| `src/pets_transformer/build.py`, `cli.py` | warning and output files, `--semantic` | 4 |
| `tests/conftest.py` | pins existing tests to `lexicon` | 3 |
| `tests/test_semantic_decide.py`, `test_semantic_model.py`, `test_detect_hybrid.py`, `test_semantic_scripts.py` | new tests | 1-6 |
| `scripts/semantic/gen_eu_tables.py` | dev and locked test tables plus their catalog | 5 |
| `scripts/semantic/llm_values.py`, `scripts/semantic/llm_values/*.json` | Featherless word lists (fake, committed) | 5 |
| `scripts/semantic/gen_corpus.py` | training corpus (jsonl, gitignored) | 5 |
| `scripts/semantic/train.py`, `scripts/semantic/TRAINING.md` | training (`--device auto/cpu/mps/cuda`) and the runbook for the teammate's Mac, with laptop and cloud fallbacks | 6 |
| `scripts/semantic/evaluate.py` | E1-E6 into `results/detect-semantic/` | 7 |
| `results/detect-semantic/*.json`, `SPLIT.md` | committed evidence | 7 |
| `README.md`, `.gitignore`, `pyproject.toml` | index rows, status line, ignores, extras | 0, 2, 5, 8 |

Tasks 1-4 (code) and Tasks 5-6 (data and training) touch different files and can run in parallel once Task 0 is done. Task 7 needs both.

---

### Task 0: Announce on main, make the fork, open the branch (zray, Sat 16:30)

**Files:**
- Modify: `README.md` (status line under "The challenge")
- Add: `plans/2026-11-07-eu-column-types.md`, `plans/2026-11-07-eu-column-types-implementation.md`

**Interfaces:** Produces: remote `fork` and branch `feat/semantic-types`, used by every later task.

- [ ] **Step 1: Add one status line to the README.** Append to the "Status (2026-11-07)" paragraph: `Work in progress on a fork (zraycd/team-1-trusted, branch feat/semantic-types): a multilingual model for column types the word lists cannot place; see plans/2026-11-07-eu-column-types.md. Main keeps the word-list detector until that work passes its checks.` The two untracked plans already in `plans/` (`next-steps-candidates`, `work-split`) are not part of this commit unless zray says so.
- [ ] **Step 2: Run tests.** Run: `.venv/bin/python -m pytest -q`. Expected: `87 passed`.
- [ ] **Step 3: Commit on main.** `git add README.md plans/2026-11-07-eu-column-types.md plans/2026-11-07-eu-column-types-implementation.md && git commit -m "Plan: EU column types, word lists first and a model for the rest (work on a fork)"` with the Co-Authored-By trailer.
- [ ] **Step 4: Push on zray's go-ahead.** Ask zray first. Then follow AGENTS.md: `git pull --rebase origin main`, `.venv/bin/python -m pytest -q`, `git push origin main`. Expected: push accepted; on rejection, go back to the pull.
- [ ] **Step 5: Make the fork and the branch.** Run: `gh repo fork alex-1121/team-1-trusted --clone=false`, then `git remote add fork https://github.com/zraycd/team-1-trusted.git`, then `git switch -c feat/semantic-types` and `git push -u fork feat/semantic-types`. Expected: `gh repo view zraycd/team-1-trusted --json isFork` prints `true`. Do not use `gh repo fork --remote`: it renames `origin`. If forking is refused (private-repo forking switched off), push the same branch to `origin` instead and note it in the PR later.

---

### Task 1: Types, decision rule and combine (pure functions)

**Files:**
- Create: `src/pets_transformer/semantic/types.py`, `src/pets_transformer/semantic/decide.py`
- Test: `tests/test_semantic_decide.py`

**Interfaces:**
- Produces, `types.py`:
  - `TYPES: tuple[str, ...] = ("PERSON_NAME", "STREET_ADDRESS", "MUNICIPALITY", "LOCATION_NAME", "ORG_NAME", "OCCUPATION", "LANGUAGE", "SEX", "FREE_TEXT", "CATEGORY")`
  - `TYPE_LABEL: dict[str, tuple[str, str]]`: PERSON_NAME and STREET_ADDRESS map to `("direct_identifier", <same>)`; MUNICIPALITY, LOCATION_NAME, ORG_NAME, OCCUPATION, LANGUAGE and SEX to `("quasi_identifier", <same>)`; FREE_TEXT to `("free_text", "FREE_TEXT")`; CATEGORY to `("non_sensitive", "CATEGORY")`.
  - `PROTECT_RANK: dict[str, int]` by role: direct_identifier 5, free_text 4, technical_identifier 3, record_key 3, quasi_identifier 2, sensitive_attribute 2, non_sensitive 0.
  - `LEXICON_RULES: dict[str, str]`: rule tag to type: `lex_municipality` MUNICIPALITY, `lex_name` PERSON_NAME, `lex_place` LOCATION_NAME, `lex_language` LANGUAGE, `lex_sex` SEX, `lex_org` ORG_NAME, `lex_occupation` OCCUPATION.
  - `type_of(role: str, subtype: str) -> str | None`: the type whose `TYPE_LABEL` equals `(role, subtype)`, else None.
- Produces, `decide.py`:
  - `@dataclass(frozen=True) class Decision: type: str; decision: str; reason: str; probs: dict[str, float]`, where `decision` is one of `"confident"`, `"protect_anyway"`, `"needs_review"`.
  - `decide(probs: dict[str, float], conf: float = 0.80, risk: float = 0.20) -> Decision`
  - `treatment(role: str, subtype: str) -> tuple`
  - `combine(role: str, subtype: str, rule: str, dec: Decision | None, agree: float = 0.30, conf: float = 0.80) -> tuple[str, str, str | None]` returns the label and a flag (`None`, `"disagree"` or `"unclear"`).

- [ ] **Step 1: Write the failing tests** in `tests/test_semantic_decide.py`:

```python
from pets_transformer.semantic.decide import Decision, combine, decide, treatment

def P(**kw):
    base = {t: 0.0 for t in ("PERSON_NAME","STREET_ADDRESS","MUNICIPALITY","LOCATION_NAME","ORG_NAME",
                             "OCCUPATION","LANGUAGE","SEX","FREE_TEXT","CATEGORY")}
    base.update(kw); return base

def test_confident_at_080():
    assert decide(P(PERSON_NAME=0.80, CATEGORY=0.20)).decision == "confident"

def test_category_055_surname_043_is_protected_not_harmless():
    d = decide(P(CATEGORY=0.55, PERSON_NAME=0.43, OCCUPATION=0.02))
    assert (d.type, d.decision) == ("PERSON_NAME", "protect_anyway")

def test_most_protective_wins_among_risky():
    d = decide(P(OCCUPATION=0.45, PERSON_NAME=0.25, CATEGORY=0.30))
    assert d.type == "PERSON_NAME"  # direct beats quasi at >= 0.20

def test_spread_without_risky_type_needs_review():
    d = decide(P(CATEGORY=0.70, PERSON_NAME=0.10, OCCUPATION=0.10, SEX=0.10))
    assert (d.type, d.decision) == ("CATEGORY", "needs_review")

def test_town_and_place_share_treatment():
    assert treatment("quasi_identifier", "MUNICIPALITY") == treatment("quasi_identifier", "LOCATION_NAME")

def test_name_and_category_differ_in_treatment():
    assert treatment("direct_identifier", "PERSON_NAME") != treatment("non_sensitive", "CATEGORY")

def test_lexicon_hit_stands_and_strong_disagreement_warns():
    dec = Decision("CATEGORY", "confident", "", P(CATEGORY=0.9, PERSON_NAME=0.1))
    assert combine("direct_identifier", "PERSON_NAME", "lex_name", dec) == ("direct_identifier", "PERSON_NAME", "disagree")

def test_lexicon_hit_with_model_support_has_no_flag():
    dec = Decision("CATEGORY", "protect_anyway", "", P(CATEGORY=0.6, PERSON_NAME=0.4))
    assert combine("direct_identifier", "PERSON_NAME", "lex_name", dec)[2] is None  # 0.40 >= 0.30

def test_fallthrough_takes_model_label():
    dec = Decision("PERSON_NAME", "confident", "", P(PERSON_NAME=0.9, CATEGORY=0.1))
    assert combine("non_sensitive", "CATEGORY", "fallthrough", dec) == ("direct_identifier", "PERSON_NAME", None)

def test_fallthrough_unclear_is_flagged():
    dec = Decision("CATEGORY", "needs_review", "", P(CATEGORY=0.7, SEX=0.1, OCCUPATION=0.1, LANGUAGE=0.1))
    assert combine("non_sensitive", "CATEGORY", "fallthrough", dec) == ("non_sensitive", "CATEGORY", "unclear")

def test_other_rule_warns_only_on_confident_more_protective_model():
    weak = Decision("PERSON_NAME", "protect_anyway", "", P(PERSON_NAME=0.5, CATEGORY=0.5))
    strong = Decision("PERSON_NAME", "confident", "", P(PERSON_NAME=0.9, CATEGORY=0.1))
    assert combine("sensitive_attribute", "DIAGNOSIS_CODE", "rule", weak)[2] is None
    assert combine("sensitive_attribute", "DIAGNOSIS_CODE", "rule", strong) == ("sensitive_attribute", "DIAGNOSIS_CODE", "disagree")

def test_no_model_means_no_change():
    assert combine("non_sensitive", "CATEGORY", "fallthrough", None) == ("non_sensitive", "CATEGORY", None)
```

- [ ] **Step 2: Run them to see them fail.** Run: `.venv/bin/python -m pytest tests/test_semantic_decide.py -q`. Expected: FAIL, `ModuleNotFoundError: pets_transformer.semantic`.
- [ ] **Step 3: Implement `types.py` and `decide.py`.** Create an empty `src/pets_transformer/semantic/__init__.py` (Task 2 fills it). The rules the tests pin:
  - `decide`: confident if the top type >= `conf`. Otherwise, among non-CATEGORY types >= `risk`, take the highest `PROTECT_RANK` of its role (ties by probability) as `protect_anyway`. Otherwise `needs_review` with the top type.
  - `reason`: a short string naming the top three types with probabilities rounded to 2 decimals. No values.
  - `treatment(role, subtype)`: `(role, tuple(json.dumps(r, sort_keys=True) for r, _ in selector.candidates(role, subtype)))`. Import `selector` inside the function, since `selector` imports `detect`, which will import this module.
  - `combine` algorithm:

```
if dec is None: return role, subtype, None
if rule == "fallthrough":
    r, s = TYPE_LABEL[dec.type]
    return r, s, ("unclear" if dec.decision == "needs_review" else None)
top = max(dec.probs, key=dec.probs.get)
if treatment(role, subtype) == treatment(*TYPE_LABEL[top]): return role, subtype, None
t = LEXICON_RULES.get(rule) or type_of(role, subtype)
if t is not None:
    return role, subtype, ("disagree" if dec.probs.get(t, 0.0) < agree else None)
more_protective = PROTECT_RANK[TYPE_LABEL[top][0]] > PROTECT_RANK[role]
return role, subtype, ("disagree" if dec.probs[top] >= conf and more_protective else None)
```

- [ ] **Step 4: Run the tests.** Run: `.venv/bin/python -m pytest tests/test_semantic_decide.py -q`. Expected: `12 passed`.
- [ ] **Step 5: Commit.** `git add src/pets_transformer/semantic tests/test_semantic_decide.py && git commit -m "semantic: type list, calibrated-decision rule and word-list/model combine"`

---

### Task 2: Features, model loader, fallback, metrics

**Files:**
- Create: `src/pets_transformer/semantic/features.py`, `model.py`, `metrics.py`; fill `__init__.py`
- Modify: `pyproject.toml`
- Test: `tests/test_semantic_model.py`

**Interfaces:**
- Consumes: `TYPES` (Task 1).
- Produces:
  - `features.N_VALUES = 64`, `features.MAX_CHARS = 256`, `features.N_SHAPE = 20`, `features.FEATURE_VERSION = 1`.
  - `sample_values(s: pd.Series, n: int = N_VALUES, seed: int = 0) -> list[str]`: non-empty stripped values, sampled without replacement with a fixed seed, each cut to `MAX_CHARS`.
  - `shape_stats(values: list[str]) -> np.ndarray` of shape `(N_SHAPE,)`, always finite. Builder picks the 20; they must cover mean and spread of length, token count, share of capitalised first letters, digits, punctuation and non-ASCII letters, distinct ratio, and the top value's share.
  - `column_vector(values: list[str], encode: Callable[[list[str]], np.ndarray]) -> np.ndarray`: `concat(mean(E), std(E), shape_stats)`, where `E = encode(["query: " + v for v in values])`. Length `2*D + N_SHAPE`.
  - `class TypeModel`: `__init__(self, encode, W: np.ndarray, b: np.ndarray, mu: np.ndarray, sigma: np.ndarray, temperature: float, types: tuple[str, ...])` and `predict_proba(self, values: list[str]) -> dict[str, float] | None`, which returns None when there are fewer than 5 values or fewer than 2 distinct ones. Probabilities are `softmax(((x - mu) / sigma) @ W + b) / temperature)` and sum to 1.
  - `model.MODEL_DIR = Path(__file__).parent / "models"`; `load_model(model_dir: Path = MODEL_DIR) -> TypeModel | None`, cached once per process. It returns None, and prints one line to stderr, when the extra, the head files or the cached encoder are missing. It loads the encoder with `SentenceTransformer(meta["encoder"], revision=meta["revision"], local_files_only=True)`.
  - `python -m pets_transformer.semantic.model --download` fetches the encoder at the pinned revision. This is the only network call, and it is explicit.
  - `available() -> bool`.
  - `__init__.resolve_mode(mode: str | None) -> str`: explicit argument, else env `PETS_SEMANTIC`, else `"hybrid"` when `available()`, else `"lexicon"`. A `"hybrid"` request without a model prints one warning and returns `"lexicon"`.
  - `metrics.ece(probs: np.ndarray, y: np.ndarray, bins: int = 10) -> float`; `metrics.reliability(probs, y, bins=10) -> list[dict]` with keys `bin`, `n`, `mean_conf`, `accuracy`.

- [ ] **Step 1: Write the failing tests** in `tests/test_semantic_model.py`. Use a stub encoder `lambda xs: np.stack([np.full(4, len(x) % 7, float) for x in xs])` and a hand-made head, so the tests never need torch:
  - `test_sample_values_deterministic_and_nonempty`: same series twice gives the same list; blanks and `""` are dropped.
  - `test_long_values_are_truncated`: a 5000-character value comes back with length 256.
  - `test_degenerate_column_features_are_finite`: `shape_stats(["a","a"])` and `column_vector(["a","a"], stub)` are all finite.
  - `test_column_vector_length`: `len == 2*4 + N_SHAPE`.
  - `test_predict_proba_sums_to_one_and_keys_are_types`: keys equal the head's types and the sum is about 1.
  - `test_temperature_softens`: with temperature 2.0 the top probability is lower than with 1.0.
  - `test_tiny_column_returns_none`: 3 values give None.
  - `test_unavailable_model_falls_back`: `load_model(tmp_path)` with an empty folder gives None; `resolve_mode("hybrid")` with `available` monkeypatched to False gives `"lexicon"`.
  - `test_env_mode_is_read`: `PETS_SEMANTIC=lexicon` makes `resolve_mode(None) == "lexicon"`.
  - `test_ece_perfect_and_bad`: one-hot correct predictions give ECE 0.0; constant 0.9 confidence at 50% accuracy gives ECE about 0.4.
- [ ] **Step 2: Run them to see them fail.** Run: `.venv/bin/python -m pytest tests/test_semantic_model.py -q`. Expected: FAIL on import.
- [ ] **Step 3: Implement the four modules and add the extras** to `pyproject.toml`: `[project.optional-dependencies] semantic = ["numpy", "sentence-transformers>=3.0"]` and `train = ["scikit-learn>=1.4", "Faker==<latest on PyPI today, exact>", "openai>=1.40", "numpy"]`. Head file format: `head.npz` holds `W, b, mu, sigma`; `meta.json` holds `encoder`, `revision`, `types`, `temperature`, `feature_version`, `n_values`, `max_chars`, `trained_on` (corpus hash and locales) and `created`. `load_model` refuses a `feature_version` other than `FEATURE_VERSION`.
- [ ] **Step 4: Run the tests.** Run: `.venv/bin/python -m pytest tests/test_semantic_model.py -q`. Expected: `10 passed`. Then the full suite: `87 + 22 passed`.
- [ ] **Step 5: Commit.** `git add pyproject.toml src/pets_transformer/semantic tests/test_semantic_model.py && git commit -m "semantic: shared features, offline model loader with lexicon fallback, calibration metrics"`

---

### Task 3: Wire the model into the detector

**Files:**
- Modify: `src/pets_transformer/detect.py`: `classify` (lines 116-224), `detect_dataset` (289-351), `main` (355-367)
- Create: `tests/conftest.py`, `tests/test_detect_hybrid.py`

**Interfaces:**
- Consumes: `combine`, `decide`, `Decision` (Task 1); `load_model`, `resolve_mode`, `sample_values` (Task 2).
- Produces:
  - `classify_traced(s: pd.Series) -> tuple[str, str, str, str]` returns `(role, subtype, kind, rule)`. `rule` is `"pre"` for every return before today's line 187, `"numeric"` for the `_classify_numeric` path, the seven `lex_*` tags from Task 1 for the word-list returns (`:187` municipality, `:189` name, `:191` place, `:193` language, `:195` sex, `:215` org, `:222` occupation), `"fallthrough"` for the final `CATEGORY` return, and `"rule"` for every other return. `classify(s)` stays `classify_traced(s)[:3]`, so every existing caller and test is unchanged.
  - `@dataclass class DetectReport: labels: pd.DataFrame; type_probs: pd.DataFrame; needs_review: pd.DataFrame; mode: str`.
    - `type_probs` columns: `dataset, table, column, rule, privacy_role, subtype, top1, p1, top2, p2, top3, p3, decision, flag`.
    - `needs_review` is the rows of `type_probs` whose `flag` is set, plus `reason`.
  - `detect_dataset_report(data_dir: Path, dataset: str, semantic: str | None = None) -> DetectReport`.
  - `detect_dataset(data_dir, dataset, semantic=None) -> pd.DataFrame` returns `detect_dataset_report(...).labels`, with the same columns as today.
  - CLI: `--semantic {lexicon,hybrid}`. It writes `<out stem>_type_probs.csv` and `<out stem>_needs_review.csv` next to `--out`, and prints `WARNING: <n> column(s) need review: <table>.<column> (<flag>), ...` when `n > 0`.

- [ ] **Step 1: Write the failing tests.** `tests/conftest.py` has an autouse fixture that sets `PETS_SEMANTIC=lexicon`, so the 87 existing tests keep today's behaviour whatever is installed. `tests/test_detect_hybrid.py` monkeypatches `pets_transformer.detect.load_model` to return a stub whose `predict_proba` returns fixed dicts chosen by a marker in the values:
  - `test_classify_traced_tags`: a HETU column is `"pre"`; a column of lexicon first names is `"lex_name"`; `["foo","bar","baz"]` cycled is `"fallthrough"`; integers are `"numeric"`.
  - `test_lexicon_mode_equals_today`: for the `tmp_path` tables from `test_detect.py`, `detect_dataset(..., "lexicon")` equals `classify`-based labels, and `type_probs` is empty.
  - `test_fallthrough_column_gets_model_label`: German names (not in the lexicon) with the stub saying PERSON_NAME 0.9 become `direct_identifier PERSON_NAME`.
  - `test_lexicon_hit_kept_and_disagreement_listed`: Finnish names with the stub saying CATEGORY 0.95 stay `PERSON_NAME`, and the column is in `needs_review` with flag `disagree`.
  - `test_tiny_column_skips_model`: a column with 3 values gets no `type_probs` row and keeps its label.
  - `test_wide_sample_path_uses_same_combine`: a table longer than `MAX_ROWS` whose first rows are blank in one column still ends with the model's label.
  - `test_outputs_hold_no_values`: every sampled value of every column is absent from the written `type_probs.csv` and `needs_review.csv` text.
  - `test_hybrid_request_without_model_runs_lexicon`: with `load_model` returning None, `detect_dataset_report(..., "hybrid").mode == "lexicon"` and the labels equal lexicon mode.
  - `test_person_table_flip_is_protective`: a table whose only person marker is a model-labelled name column is not demoted to reference data.
- [ ] **Step 2: Run them to see them fail.** Run: `.venv/bin/python -m pytest tests/test_detect_hybrid.py -q`. Expected: FAIL, `classify_traced` not defined.
- [ ] **Step 3: Implement.** Split today's `classify` body at line 187 into a helper for the part before (returns a label or None) and one for the rest. Tag each return as listed. In `detect_dataset_report`, wrap the per-column step (both the head rows and the wide-sample second look) in one function: `classify_traced`, then, when the mode is hybrid and the rule is neither `pre` nor `numeric`, `model.predict_proba(sample_values(series))`, then `decide`, then `combine`. Table-context logic (keys, foreign keys, `person`, reference demotion) runs after, unchanged, on the combined labels. Import `load_model` at module level from `.semantic.model` so tests can patch `pets_transformer.detect.load_model`.
- [ ] **Step 4: Run all tests.** Run: `.venv/bin/python -m pytest -q`. Expected: all pass (`87 + 22 + 9`).
- [ ] **Step 5: Commit.** `git add src/pets_transformer/detect.py tests/conftest.py tests/test_detect_hybrid.py && git commit -m "detect: hybrid mode, word-list label stands, model labels the fall-through, warnings on disagreement"`

---

### Task 4: Warnings and files in `build` and the CLI

**Files:**
- Modify: `src/pets_transformer/build.py:18`, `:47-48`, `:96`; `src/pets_transformer/cli.py` (build parser and its call)
- Test: `tests/test_wiring.py`

**Interfaces:**
- Consumes: `detect_dataset_report`, `DetectReport` (Task 3).
- Produces:
  - `build.run(..., semantic: str | None = None)`.
  - `build.report_review(reports: list[DetectReport], results: Path) -> str`: writes `results/type_probs.csv` and `results/needs_review.csv` (both gitignored by `results/**/*.csv`) and returns the warning line, or `""`.
  - `cli build --semantic {lexicon,hybrid}`.

- [ ] **Step 1: Write the failing tests** in `tests/test_wiring.py`:
  - `test_report_review_writes_files_and_warns`: two hand-made reports, one with two flagged rows (one from `unseen`). Both CSVs exist; the returned line starts with `WARNING: 2 column(s) need review` and names both columns.
  - `test_report_review_silent_when_clean`: no flags gives `""` and an empty-with-header `needs_review.csv`.
  - `test_cli_build_accepts_semantic_flag`: argparse accepts `--semantic lexicon`.
- [ ] **Step 2: Run them to see them fail.** Run: `.venv/bin/python -m pytest tests/test_wiring.py -q`. Expected: the three new tests FAIL.
- [ ] **Step 3: Implement.** `build.run` calls `detect_dataset_report` for the original and for `unseen` with the same `semantic`, calls `report_review`, and prints its line. The build never stops for a review flag (spec decision). Pass the labels on exactly as today.
- [ ] **Step 4: Run all tests.** Run: `.venv/bin/python -m pytest -q`. Expected: all pass.
- [ ] **Step 5: Commit.** `git add src/pets_transformer/build.py src/pets_transformer/cli.py tests/test_wiring.py && git commit -m "build: print and save columns that need review; --semantic flag"`

---

### Task 5: Test tables and the training corpus (fake data only, Sat 18:30)

**Files:**
- Create: `scripts/semantic/gen_eu_tables.py` (from the scratch `gen_faker.py`), `scripts/semantic/llm_values.py`, `scripts/semantic/llm_values/<lang>.json`, `scripts/semantic/gen_corpus.py`
- Modify: `.gitignore` (add `data/semantic-eval/` and `data/semantic-corpus/`)
- Test: `tests/test_semantic_scripts.py`

**Interfaces:**
- Produces:
  - `gen_eu_tables.py --out data/semantic-eval --split dev|locked` writes `<locale>/customers.csv` and `catalog.csv` (proving-ground catalog format).
    - dev: the 8 locales `fi_FI de_DE fr_FR pl_PL it_IT es_ES nl_NL sv_SE`, seed 7, plus one mixed table `mixed_EU` whose name, town and occupation columns draw from all 8 locales.
    - locked: `cs_CZ pt_PT hu_HU`, seed 99.
    - The 22 columns and labels are exactly as in the scratch generator (valid DE tax IDs, ES NIFs, SE IBANs; local date formats).
  - `gen_corpus.LOCKED = ("cs_CZ", "pt_PT", "hu_HU")`, `gen_corpus.CALIB = ("sk_SK", "ro_RO", "el_GR")`.
  - `gen_corpus.train_locales() -> list[str]`: every EU locale Faker has (also `de_AT`, `nl_BE`, `en_IE`, `fr_BE` if present), minus `LOCKED`.
  - `gen_corpus.py --out data/semantic-corpus --per-type 60 --seed 1000` writes `train.jsonl`, `calib.jsonl` and `locked.jsonl`.
    - The first line of each file is `{"corpus": "pets_transformer.semantic", "synthetic": true, "version": 1, "seed": ..., "faker": "<version>"}`.
    - `gen_corpus.py` prints the SHA-256 of each file it writes, so two machines can check they made the same corpus.
    - Each next line is `{"locale", "type", "values": [...<= 64]}`.
  - `llm_values.py --model <featherless model id> --langs ...` calls `https://api.featherless.ai/v1` with key `FEATHERLESS_API_KEY` from the environment. It asks, per language, for lists of occupations, sex and gender words, language names, clinic and department names, and harmless category words (statuses, product types, triage words). It writes `llm_values/<lang>.json`. The prompts name no person and send no data.

- [ ] **Step 1: Write the failing tests** in `tests/test_semantic_scripts.py`, skipped when Faker is missing (`pytest.importorskip("faker")`):
  - `test_locked_locales_never_in_training`: `set(train_locales()) & set(LOCKED) == set()`.
  - `test_corpus_header_and_schema`: a run with `--per-type 2` into `tmp_path` writes the header line with `synthetic: true`; every record's `type` is in `TYPES` and has at most 64 values.
  - `test_dev_tables_deterministic`: two runs of `gen_eu_tables --split dev` give identical `de_DE/customers.csv`.
  - `test_catalog_matches_columns`: every catalog row names an existing column.
- [ ] **Step 2: Run them to see them fail.** Run: `.venv/bin/python -m pytest tests/test_semantic_scripts.py -q`. Expected: FAIL on import.
- [ ] **Step 3: Implement the generators.**
  - Corpus column variety: pool size drawn per column (2 to 4 values for SEX, 5 to 40 for CATEGORY and LANGUAGE, hundreds for names), Zipf weights, then noise (upper, lower or title case, 0 to 10% blanks, stray spaces, a title such as "Dr." on some names).
  - Sources per type: Faker for names, streets, addresses, cities, regions and countries, companies and jobs; Faker sentences plus LLM lists for FREE_TEXT; LLM lists for OCCUPATION in the local language, SEX, LANGUAGE (names and lower-case ISO codes), ORG_NAME (clinics) and CATEGORY.
  - Run `llm_values.py` once for the 24 languages of the training locales (check the model id and the price per call on Featherless first; stop if the $25 would run out). Then run `gen_corpus.py`. Both run on the laptop: generation is not training. Commit the corpus hashes in `results/detect-semantic/corpus.json` so the training machine can check its own copy.
- [ ] **Step 4: Run the tests.** Run: `.venv/bin/python -m pytest tests/test_semantic_scripts.py -q`. Expected: `4 passed`.
- [ ] **Step 5: Freeze the test sets and commit.** Generate `--split dev` and `--split locked` into `data/semantic-eval/` (gitignored). Record their SHA-256 hashes and the Faker version in `results/detect-semantic/test_sets.json`. Do not open the locked tables. Then `git add .gitignore scripts/semantic tests/test_semantic_scripts.py results/detect-semantic/test_sets.json results/detect-semantic/corpus.json && git commit -m "semantic: fake EU test tables, Featherless word lists, training corpus generator"`

---

### Task 6: Train on the teammate's M5 MacBook (Sat 20:30)

**Files:**
- Create: `scripts/semantic/train.py`, `scripts/semantic/TRAINING.md`, `src/pets_transformer/semantic/models/head.npz`, `src/pets_transformer/semantic/models/meta.json`
- Test: `tests/test_semantic_scripts.py`

**Interfaces:**
- Consumes: `column_vector`, `sample_values`, `FEATURE_VERSION`, `N_VALUES`, `MAX_CHARS` (Task 2); corpus files (Task 5).
- Produces: `train.py --corpus <dir> --out <dir> [--encoder intfloat/multilingual-e5-small --revision <sha>] [--device auto|cpu|mps|cuda] [--cache <dir>]` writes `head.npz` and `meta.json` in the format Task 2's `load_model` reads, and `train_report.json` (per-type F1 on `calib`, chosen temperature, ECE on `calib`). It trains a multinomial `LogisticRegression` (scikit-learn, standardised features) on `train.jsonl`, then fits the temperature on `calib.jsonl` by minimising negative log-likelihood over a grid from 0.5 to 5.0. `locked.jsonl` is not read. `--device auto` picks `cuda`, then `mps`, then `cpu`. Unique values are encoded once and their vectors cached under `--cache` (default `<corpus>/.emb/`, keyed by encoder revision and value hash), so a retrain in Task 7 does not encode again. `meta.json` also records the device and the corpus SHA-256 hashes.

- [ ] **Step 1: Write the failing tests** (skipped without scikit-learn):
  - `test_train_refuses_non_corpus_input`: a folder holding a CSV, or a jsonl whose first line lacks `"synthetic": true`, makes `train.py` exit non-zero with `not a pets_transformer.semantic corpus`. A path under `data/proving-ground` is refused the same way.
  - `test_train_roundtrip_with_stub_encoder`: a 3-type, 6-column corpus and a stub encoder (`--encoder stub`, test-only) write a head that `TypeModel` loads and that predicts the training type for a training column.
- [ ] **Step 2: Run them to see them fail.** Run: `.venv/bin/python -m pytest tests/test_semantic_scripts.py -q -k train`. Expected: FAIL.
- [ ] **Step 3: Implement `train.py` and write `TRAINING.md`.** The runbook has these steps, in order:
  1. zray pins the encoder: `python -c "from huggingface_hub import HfApi; print(HfApi().model_info('intfloat/multilingual-e5-small').sha)"`. Check the licence on the model card is MIT.
  2. On zray's laptop, a timing run: `train.py --corpus <a --per-type 10 corpus> --device cpu`. It prints values per second; this decides whether the laptop is a usable fallback.
  3. The teammate, on the M5 MacBook: `git clone https://github.com/zraycd/team-1-trusted.git -b feat/semantic-types`, then `python3 -m venv v && v/bin/pip install -e '.[semantic,train]'`, then `v/bin/python -m pets_transformer.semantic.model --download`.
  4. The teammate generates the corpus with the same command and seed as Task 5 and checks that the printed hashes equal `results/detect-semantic/corpus.json`. On a mismatch, stop: the Faker version or the word lists differ.
  5. The teammate runs `v/bin/python scripts/semantic/train.py --corpus data/semantic-corpus --out models --revision <sha> --device mps`.
  6. The teammate sends zray `models/head.npz`, `models/meta.json` and `models/train_report.json` (AirDrop or chat; under 2 MB). Nothing else comes back and nothing else goes there: no `data/proving-ground/`, `data/semantic-eval/`, `results/` or `out/`.
  7. Fallbacks, in order: the same commands on zray's laptop with `--device cpu`; then a cloud GPU (Vultr or Google Cloud; create in the web console, copy only `pyproject.toml`, `src/pets_transformer/`, `scripts/semantic/` and the corpus, destroy the machine when done and note the cost).
- [ ] **Step 4: Run it.** Run the tests on the laptop (`2 passed` plus a device test: `--device cpu` works without torch's `mps`); then run the runbook. Expected: `train_report.json` with per-type F1 on `calib` and ECE; `head.npz` under 2 MB; `meta.json` corpus hashes equal `corpus.json`.
- [ ] **Step 5: Install on the laptop and commit.** `.venv/bin/pip install -e .[semantic]` and `.venv/bin/python -m pets_transformer.semantic.model --download`. Then `git add scripts/semantic/train.py scripts/semantic/TRAINING.md src/pets_transformer/semantic/models tests/test_semantic_scripts.py results/detect-semantic/train_report.json && git commit -m "semantic: trained head (fake EU corpus, calibrated on held-out locales) and training runbook"`

---

### Task 7: Evaluate, one round of fixes on the development set, then the test set once

**Files:**
- Create: `scripts/semantic/evaluate.py`, `results/detect-semantic/SPLIT.md`, `results/detect-semantic/*.json`

**Interfaces:**
- Consumes: `detect_dataset_report` (Task 3), `ece`/`reliability` (Task 2), `pets_eval.detect.score_detection`, test tables (Task 5).
- Produces: `evaluate.py --split dev|test --out results/detect-semantic`. It runs both modes and writes:
  - `e1_proving_ground_<split>.json`: role macro-F1, accuracy, subtype accuracy, per-role table. Dev is the six tuning datasets; test is health, public_admin and customer_service.
  - `e2_eu_<split>.json`, per locale:
    - macro-F1;
    - the count of model-type columns labelled `non_sensitive` (gate: at most 1);
    - number-format columns reported separately.
  - `e2b_unseen.json`: every unseen column whose label differs between modes, with both labels and its flag. No values.
  - `e3_calibration_<split>.json`: ECE and the reliability table on columns of model types. Dev is `calib` plus the dev tables; test is `locked.jsonl` plus the locked tables.
  - `e4_warnings_<split>.json`: needs-review count and share per dataset.
  - `e5_cost.json`: wall-clock seconds for detect on all nine proving-ground datasets, both modes, this laptop.

  Every file also records the commit, the encoder revision, the thresholds and the time.

- [ ] **Step 1: Write `SPLIT.md` before any run.** It says:
  - which data is development and which is test, as in the spec;
  - that the test split is run once;
  - that anything changed after a test run is listed below that line.
- [ ] **Step 2: Implement and run the development split.** Run: `.venv/bin/python scripts/semantic/evaluate.py --split dev --out results/detect-semantic`. Expected: all dev JSON files written. Read the errors.
- [ ] **Step 3: One round of fixes (until Sun 03:00).** Change only thresholds inside the spec's rules, corpus noise or sources, and retrains through Task 6's runbook (with the embedding cache, a retrain with unchanged values does not re-encode). Each retrain gets a line in `SPLIT.md`. Rerun Step 2.
- [ ] **Step 4: Run the test split once.** Run: `.venv/bin/python scripts/semantic/evaluate.py --split test --out results/detect-semantic`. Expected:
  - E1: no held-out dataset below 0.8202 / 0.7241 / 0.7821.
  - E2: at most 1 model-type column harmless per locked country.
  - E3: ECE at most 0.05.
  - E4: about 1 in 10 columns or fewer flagged on the proving ground.
  - E5: hybrid at most 3 times lexicon.

  Write down any miss as a miss. Do not rerun the test split.
- [ ] **Step 5: Commit.** `git add scripts/semantic/evaluate.py results/detect-semantic && git commit -m "semantic: evaluation on dev and test splits (E1-E5), split protocol"`

---

### Task 8: README, PR, go or no-go (Sun 08:00)

**Files:**
- Modify: `README.md` ("Layout" rows if a top-level path is new; "How to run" gets the `[semantic]` install, the `--download` step and `--semantic`; demo item 1 gets the E1/E2 numbers with their JSON file names), `results/detect-semantic/README.md` (what each JSON is)

- [ ] **Step 1: Write the README changes,** with every number followed by its JSON file. Add the spec's limitations in plain words (trained on fake data; a word-list match is trusted; number formats are the next step; warnings do not block).
- [ ] **Step 2: Full check.** Run: `.venv/bin/python -m pytest -q` (all pass), then `.venv/bin/python -m pets_transformer.cli build --scenario HEALTH-S1 --out /tmp/hs1 --results /tmp/hs1res --submission /tmp/hs1sub`. Expected: gate pass, plus a warning line if anything is flagged.
- [ ] **Step 3: Go or no-go.**
  - **Go,** if E1-E6 pass (E6 = the full test suite): ask zray, then `git fetch origin && git rebase origin/main`, rerun the tests, `git push --force-with-lease fork feat/semantic-types`, and `gh pr create --repo alex-1121/team-1-trusted --head zraycd:feat/semantic-types --base main`. The PR body lists E1-E6 with their JSON files, what was not checked, and the attribution line.
  - **No-go:** no PR. Send the team (track 2, Tadek) one paragraph for the video and README: the idea, the committed numbers, "work in progress on a fork".
- [ ] **Step 4: Commit any README fix** made during Step 2 in its own commit before the push.

---

## Self-review notes

- Spec coverage:
  - Goals 1-5: Tasks 1-3 (types, decision, combine), 2 (calibration, offline), 3-4 (warnings, files), 7 (scores).
  - Non-goals: untouched; no task edits the selector, protect, repair, red team or score logic.
  - Anti-goals: Global Constraints; Review Focus items 2 and 5.
  - Fork and announce: Task 0. Schedule: task headers. Limitations: Task 8.
- The disagreement rule for labels from rules outside the model's types (a confident, more protective model type warns) is this plan's reading of the spec's "P(L's type) < 0.30" for labels that have no model type. It keeps warnings on ID, diagnosis and key columns rare (E4).
