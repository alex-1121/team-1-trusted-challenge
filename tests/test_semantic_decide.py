from pets_transformer.semantic.decide import Decision, combine, decide, treatment


def P(**kw):
    base = {t: 0.0 for t in ("PERSON_NAME", "STREET_ADDRESS", "MUNICIPALITY", "LOCATION_NAME", "ORG_NAME",
                             "OCCUPATION", "LANGUAGE", "SEX", "FREE_TEXT", "CATEGORY")}
    base.update(kw)
    return base


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


def test_reason_names_top_three_types_only():
    d = decide(P(CATEGORY=0.55, PERSON_NAME=0.43, OCCUPATION=0.02))
    assert d.reason == "CATEGORY 0.55, PERSON_NAME 0.43, OCCUPATION 0.02"


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
