"""Word lists per language from a model on Featherless (OpenAI-compatible API), for the fake training corpus.

    set -a; . ./.env; set +a
    python scripts/semantic/llm_values.py --model Qwen/Qwen2.5-72B-Instruct --langs fi de sv
    python scripts/semantic/llm_values.py --model Qwen/Qwen2.5-72B-Instruct --all

The prompts ask for general vocabulary (job titles, town names, words for 'female', status words ...). They name no
person and carry no data: nothing from the proving ground or any real file is ever sent. The answers are written
to scripts/semantic/llm_values/<lang>.json and committed; the corpus generator reads them offline. A language
whose file already holds a kind is skipped, so the script can be rerun after a failure.
"""
import argparse
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from locales import languages  # noqa: E402

OUT = Path(__file__).parent / "llm_values"
BASE_URL = "https://api.featherless.ai/v1"
CATEGORY_GROUPS = ["order or case status", "priority level", "product type", "contact channel",
                   "triage level in an emergency department", "yes and no style answers", "payment method",
                   "colour", "weekday", "month", "clothing size", "satisfaction rating",
                   "insurance plan tier", "ticket category in customer service", "vehicle type", "blood group"]
KINDS = {  # kind: (what to ask for, how many)
    "occupations": ("job titles (occupations) as written on a form, varied across sectors and skill levels", 80),
    "towns": ("names of real towns and cities, big and small, from all regions of {country}", 80),
    "regions": ("names of regions, provinces, counties or districts of {country}", 25),
    "countries": ("names of countries of the world, as written in {lang}", 40),
    "language_names": ("names of languages of the world, as written in {lang}", 40),
    "orgs": ("names of fictional but realistic organisations: clinics, hospital departments, companies, shops, "
             "schools and associations, as they would appear in {country}", 60),
    "notes": ("short fictional free-text notes (1 to 3 sentences, varied length) as written by staff in a "
              "customer-service log or a clinical record; do not include any person's name", 40),
}


def prompt(kind: str, lang: str, country: str) -> str:
    if kind == "sex":
        return (f"In {lang}, list the words and short codes used in forms and databases for a person's sex or "
                f"gender. Return JSON with keys female, male, other, unknown; each an array of strings in {lang} "
                f"(full words, abbreviations, one-letter codes).")
    if kind == "categories":
        groups = "; ".join(CATEGORY_GROUPS)
        return (f"In {lang}, give typical category values used in business databases for each of these groups: "
                f"{groups}. Return JSON: an object whose keys are the English group names and whose values are "
                f"arrays of 3 to 10 short strings in {lang}.")
    what, n = KINDS[kind]
    return (f"List {n} {what.format(lang=lang, country=country)}. Write them in {lang}. "
            f"Return JSON: an object with key \"values\", an array of strings. No numbering, no explanations.")


def strings_after_bracket(text: str) -> list:
    """Every complete JSON string after the first '[': a list cut off at max_tokens or with a stray comma."""
    body = text.split("[", 1)[1]
    return [json.loads(f'"{x}"', strict=False) for x in re.findall(r'"((?:[^"\\]|\\.)*)"', body)]


def parse(text: str):
    for pat, wrap in ((r"\{.*\}", False), (r"\[.*\]", True)):
        m = re.search(pat, text, re.S)
        if m:
            try:
                obj = json.loads(m.group(0), strict=False)
                return {"values": obj} if wrap else obj
            except json.JSONDecodeError:
                break
    if "[" in text and ":" not in text.split("[", 1)[1]:  # a flat list: salvage its whole strings
        vals = strings_after_bracket(text)
        if vals:
            return {"values": vals}
    raise ValueError(f"no JSON object in the answer: {text[:80]!r}")


def clean(kind: str, obj):
    def strings(xs):
        return sorted({x.strip() for x in xs if isinstance(x, str) and x.strip() and len(x.strip()) < 400})
    if kind in ("sex", "categories"):
        return {k: strings(v) for k, v in obj.items() if isinstance(v, list) and strings(v)}
    return strings(obj["values"])


def ask(client, model: str, text: str, tries: int = 3):
    for i in range(tries):
        try:
            r = client.chat.completions.create(model=model, temperature=0.4, max_tokens=3000,
                                               messages=[{"role": "user", "content": text}])
            if not r.choices or not r.choices[0].message.content:
                raise RuntimeError("empty reply")
            return r.choices[0].message.content, r.usage
        except Exception as e:  # noqa: BLE001 (network drop, empty reply or rate limit: wait and retry)
            if i == tries - 1:
                raise
            print(f"  retry after {type(e).__name__}: {str(e)[:120]}", file=sys.stderr, flush=True)
            time.sleep(10 * (i + 1))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--model", required=True)
    ap.add_argument("--langs", nargs="*", default=[])
    ap.add_argument("--all", action="store_true", help="every language of every EU locale (held-out ones too)")
    ap.add_argument("--kinds", nargs="*", default=list(KINDS) + ["sex", "categories"])
    ap.add_argument("--workers", type=int, default=2, help="languages fetched in parallel")
    ap.add_argument("--timeout", type=float, default=150, help="seconds per call before giving up")
    a = ap.parse_args(argv)
    from openai import OpenAI
    key = os.environ.get("FEATHERLESS_API_KEY")
    if not key:
        sys.exit("FEATHERLESS_API_KEY is not set (set -a; . ./.env; set +a)")
    client = OpenAI(base_url=BASE_URL, api_key=key, timeout=a.timeout, max_retries=0)
    langs = languages()
    todo = sorted(langs) if a.all else a.langs
    OUT.mkdir(exist_ok=True)
    tokens, lock = [0, 0], threading.Lock()

    def one(code):
        name, country = langs[code]
        path = OUT / f"{code}.json"
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        for kind in a.kinds:
            if data.get(kind):
                continue
            try:
                text, usage = ask(client, a.model, prompt(kind, name, country))
                data[kind] = clean(kind, parse(text))
                with lock:  # workers run in threads; += on a shared list is not atomic
                    tokens[0] += usage.prompt_tokens
                    tokens[1] += usage.completion_tokens
            except Exception as e:  # noqa: BLE001 (keep what we have; a rerun fills the gap)
                print(f"{code} {kind}: FAILED {type(e).__name__}: {str(e)[:120]}", file=sys.stderr, flush=True)
                continue
            n = len(data[kind]) if isinstance(data[kind], list) else sum(map(len, data[kind].values()))
            print(f"{code} {kind}: {n}", flush=True)
            models = data.get("_meta", {}).get("models", {})
            models[kind] = a.model
            data["_meta"] = {"language": name, "country": country, "models": models, "source": "featherless.ai",
                             "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
            path.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    with ThreadPoolExecutor(a.workers) as pool:
        list(pool.map(one, todo))
    print(f"tokens: {tokens[0]} in, {tokens[1]} out")


if __name__ == "__main__":
    main()
