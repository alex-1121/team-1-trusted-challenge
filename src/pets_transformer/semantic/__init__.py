"""Column types from a small multilingual model, for the columns the word lists cannot place."""
import os

from .model import available, load_model

MODES = ("lexicon", "hybrid")


def requested_mode(mode: str | None) -> str | None:
    """Explicit argument, else env PETS_SEMANTIC; None means "hybrid if the model loads"."""
    mode = mode or os.environ.get("PETS_SEMANTIC") or None
    if mode is not None and mode not in MODES:
        raise ValueError(f"semantic mode must be one of {MODES}, got {mode!r}")
    return mode


def resolve_mode(mode: str | None) -> str:
    """requested_mode, then hybrid only when the model loads. A hybrid request without a model falls back to
    lexicon; load_model has then printed the one warning line."""
    if requested_mode(mode) == "lexicon":
        return "lexicon"
    return "hybrid" if available() else "lexicon"
