"""Column types the model can give, and how each maps onto the detector's (role, subtype) labels.

The model only knows the types the word lists try to place (names, places, organisations, occupations, languages,
sex), plus free text and harmless categories. Every other label (codes, dates, numbers, keys) comes from rules.
"""

TYPES: tuple[str, ...] = ("PERSON_NAME", "STREET_ADDRESS", "MUNICIPALITY", "LOCATION_NAME", "ORG_NAME",
                          "OCCUPATION", "LANGUAGE", "SEX", "FREE_TEXT", "CATEGORY")

TYPE_LABEL: dict[str, tuple[str, str]] = {
    "PERSON_NAME": ("direct_identifier", "PERSON_NAME"),
    "STREET_ADDRESS": ("direct_identifier", "STREET_ADDRESS"),
    "MUNICIPALITY": ("quasi_identifier", "MUNICIPALITY"),
    "LOCATION_NAME": ("quasi_identifier", "LOCATION_NAME"),
    "ORG_NAME": ("quasi_identifier", "ORG_NAME"),
    "OCCUPATION": ("quasi_identifier", "OCCUPATION"),
    "LANGUAGE": ("quasi_identifier", "LANGUAGE"),
    "SEX": ("quasi_identifier", "SEX"),
    "FREE_TEXT": ("free_text", "FREE_TEXT"),
    "CATEGORY": ("non_sensitive", "CATEGORY"),
}

# How much protection a role needs, higher first. Used to pick the safest of several likely types.
PROTECT_RANK: dict[str, int] = {"direct_identifier": 5, "free_text": 4, "technical_identifier": 3, "record_key": 3,
                                "quasi_identifier": 2, "sensitive_attribute": 2, "non_sensitive": 0}

# Word-list rule tag (from detect.classify_traced) to the type that rule claims.
LEXICON_RULES: dict[str, str] = {"lex_municipality": "MUNICIPALITY", "lex_name": "PERSON_NAME",
                                 "lex_place": "LOCATION_NAME", "lex_language": "LANGUAGE", "lex_sex": "SEX",
                                 "lex_org": "ORG_NAME", "lex_occupation": "OCCUPATION"}


def type_of(role: str, subtype: str) -> str | None:
    """The model type whose label is (role, subtype), else None."""
    for t, label in TYPE_LABEL.items():
        if label == (role, subtype):
            return t
    return None
