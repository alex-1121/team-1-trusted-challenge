"""Turn the model's probabilities into a type, and combine it with the word-list label.

decide: confident when the top type has at least `conf`. Otherwise any risky type (not CATEGORY) with at least
`risk` is protected anyway, the most protective one first. Otherwise the column needs review.

combine: a word-list or rule label stands; the model only labels columns that fell through to CATEGORY. A flag
says when a person should look: "disagree" when the model doubts a label in a way that changes its treatment,
"unclear" when the model could not settle a fall-through column. Probabilities and type names only, never values.
"""
import functools
import json
from dataclasses import dataclass

from .types import LEXICON_RULES, PROTECT_RANK, TYPE_LABEL, type_of


@dataclass(frozen=True)
class Decision:
    type: str
    decision: str  # "confident", "protect_anyway" or "needs_review"
    reason: str
    probs: dict[str, float]


def decide(probs: dict[str, float], conf: float = 0.80, risk: float = 0.20) -> Decision:
    ranked = sorted(probs, key=probs.get, reverse=True)
    reason = ", ".join(f"{t} {probs[t]:.2f}" for t in ranked[:3])
    top = ranked[0]
    if probs[top] >= conf:
        return Decision(top, "confident", reason, probs)
    risky = [t for t in ranked if t != "CATEGORY" and probs[t] >= risk]
    if risky:
        best = max(risky, key=lambda t: (PROTECT_RANK[TYPE_LABEL[t][0]], probs[t]))
        return Decision(best, "protect_anyway", reason, probs)
    return Decision(top, "needs_review", reason, probs)


@functools.lru_cache(maxsize=None)
def treatment(role: str, subtype: str) -> tuple:
    """What the selector would do with a column of this label: two labels with the same treatment are equivalent."""
    from .. import selector  # selector imports detect, which imports this module
    return role, tuple(json.dumps(r, sort_keys=True) for r, _ in selector.candidates(role, subtype))


def combine(role: str, subtype: str, rule: str, dec: Decision | None, agree: float = 0.30,
            conf: float = 0.80) -> tuple[str, str, str | None]:
    if dec is None:
        return role, subtype, None
    if rule == "fallthrough":
        r, s = TYPE_LABEL[dec.type]
        return r, s, ("unclear" if dec.decision == "needs_review" else None)
    top = max(dec.probs, key=dec.probs.get)
    if treatment(role, subtype) == treatment(*TYPE_LABEL[top]):
        return role, subtype, None
    t = LEXICON_RULES.get(rule) or type_of(role, subtype)
    if t is not None:
        return role, subtype, ("disagree" if dec.probs.get(t, 0.0) < agree else None)
    more_protective = PROTECT_RANK[TYPE_LABEL[top][0]] > PROTECT_RANK[role]
    return role, subtype, ("disagree" if dec.probs[top] >= conf and more_protective else None)
