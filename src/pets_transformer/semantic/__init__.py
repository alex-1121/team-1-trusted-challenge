"""Column types from a small multilingual model, for the columns the word lists cannot place."""
import os

from .model import load_model

MODES = ("lexicon", "advisor", "hybrid")


def requested_mode(mode: str | None) -> str | None:
    """Explicit argument, else env PETS_SEMANTIC; None means "advisor if the model loads"."""
    mode = mode or os.environ.get("PETS_SEMANTIC") or None
    if mode is not None and mode not in MODES:
        raise ValueError(f"semantic mode must be one of {MODES}, got {mode!r}")
    return mode


class ModelUnavailable(RuntimeError):
    """advisor or hybrid was asked for explicitly (argument or PETS_SEMANTIC) but the model did not load."""


def resolve(mode: str | None, load=load_model):
    """(mode that runs, model or None). requested_mode, else advisor when the model loads, else lexicon.

    advisor (the default): labels are the word lists' labels, unchanged; the model only adds review flags.
    hybrid: the model also labels the columns the word lists cannot place (better on non-Finnish data, slightly
    worse on the proving ground's held-out datasets: results/detect-semantic/e1_proving_ground_test.json).

    Only the unrequested default falls back to lexicon (load_model has then printed one warning line). A mode asked
    for by name raises ModelUnavailable, so a broken install never turns a requested model run into a word-list run
    without anyone noticing."""
    want = requested_mode(mode)
    if want == "lexicon":
        return "lexicon", None
    model = load()
    if model is not None:
        return want or "advisor", model
    if want is not None:
        raise ModelUnavailable(f"semantic mode {want!r} was requested but the model is unavailable (see the warning "
                               "above); install it or ask for lexicon")
    return "lexicon", None


def resolve_mode(mode: str | None) -> str:
    return resolve(mode, load_model)[0]


def available() -> bool:
    return load_model() is not None
