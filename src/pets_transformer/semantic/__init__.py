"""Column types from a small multilingual model, for the columns the word lists cannot place."""
import os

from .model import available, load_model

MODES = ("lexicon", "advisor", "hybrid")


def requested_mode(mode: str | None) -> str | None:
    """Explicit argument, else env PETS_SEMANTIC; None means "advisor if the model loads"."""
    mode = mode or os.environ.get("PETS_SEMANTIC") or None
    if mode is not None and mode not in MODES:
        raise ValueError(f"semantic mode must be one of {MODES}, got {mode!r}")
    return mode


def resolve_mode(mode: str | None) -> str:
    """requested_mode, else advisor; any mode but lexicon needs the model. Without it the request falls back to
    lexicon; load_model has then printed the one warning line.

    advisor (the default): labels are the word lists' labels, unchanged; the model only adds review flags.
    hybrid: the model also labels the columns the word lists cannot place (better on non-Finnish data, slightly
    worse on the proving ground's held-out datasets: results/detect-semantic/e1_proving_ground_test.json)."""
    want = requested_mode(mode) or "advisor"
    if want == "lexicon":
        return "lexicon"
    return want if available() else "lexicon"
