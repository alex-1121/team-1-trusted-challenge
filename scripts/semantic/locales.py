"""EU locales Faker has, their language and country, and which are held out (shared by the generators)."""

# locale: (ISO 639-1 language, language name in English, country in English)
LOCALES = {
    "bg_BG": ("bg", "Bulgarian", "Bulgaria"), "cs_CZ": ("cs", "Czech", "Czechia"),
    "da_DK": ("da", "Danish", "Denmark"), "de_AT": ("de", "German", "Austria"), "de_DE": ("de", "German", "Germany"),
    "de_LU": ("de", "German", "Luxembourg"), "el_CY": ("el", "Greek", "Cyprus"), "el_GR": ("el", "Greek", "Greece"),
    "en_IE": ("en", "English", "Ireland"), "es_ES": ("es", "Spanish", "Spain"), "et_EE": ("et", "Estonian", "Estonia"),
    "fi_FI": ("fi", "Finnish", "Finland"), "fr_BE": ("fr", "French", "Belgium"), "fr_FR": ("fr", "French", "France"),
    "ga_IE": ("ga", "Irish", "Ireland"), "hr_HR": ("hr", "Croatian", "Croatia"),
    "hu_HU": ("hu", "Hungarian", "Hungary"), "it_IT": ("it", "Italian", "Italy"),
    "lb_LU": ("lb", "Luxembourgish", "Luxembourg"), "lt_LT": ("lt", "Lithuanian", "Lithuania"),
    "lv_LV": ("lv", "Latvian", "Latvia"), "mt_MT": ("mt", "Maltese", "Malta"), "nl_BE": ("nl", "Dutch", "Belgium"),
    "nl_NL": ("nl", "Dutch", "Netherlands"), "pl_PL": ("pl", "Polish", "Poland"),
    "pt_PT": ("pt", "Portuguese", "Portugal"), "ro_RO": ("ro", "Romanian", "Romania"),
    "sk_SK": ("sk", "Slovak", "Slovakia"), "sl_SI": ("sl", "Slovenian", "Slovenia"),
    "sv_SE": ("sv", "Swedish", "Sweden"),
}
# Test: never in training or tuning. Calibration: held out from training, used to fit the temperature.
LOCKED = ("cs_CZ", "pt_PT", "hu_HU")
CALIB = ("sk_SK", "ro_RO", "el_GR")


def lang(loc: str) -> str:
    return LOCALES[loc][0]


def train_locales() -> list[str]:
    """Every EU locale minus the locked and calibration ones, and minus any locale sharing their language
    (el_CY would leak Greek into training)."""
    held = {lang(loc) for loc in LOCKED + CALIB}
    return [loc for loc in sorted(LOCALES) if lang(loc) not in held]


def languages() -> dict[str, tuple[str, str]]:
    """language code: (language name, one country), for every language of every locale, held-out ones included."""
    out = {}
    for loc, (code, name, country) in sorted(LOCALES.items()):
        out.setdefault(code, (name, country))
    return out


def stable_faker(loc: str):
    """Faker for one locale with every list in a fixed order. Faker builds the it_IT city list from a set, whose
    order changes with the process's hash seed; sorting it makes a seeded run give the same bytes every time."""
    from faker import Faker
    f = Faker(loc)
    for p in f.providers:
        if isinstance(getattr(p, "cities", None), list):
            p.cities = sorted(p.cities)
    return f
