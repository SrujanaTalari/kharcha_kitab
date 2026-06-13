"""
i18n.py — Internationalization & Localization utilities
Supports: English (en), Hindi (hi), Telugu (te)
"""
import json
import os
from datetime import date, datetime
from babel.numbers import format_currency, format_number
from babel.dates import format_date

_cache: dict = {}

SUPPORTED_LANGS = {
    "English": "en",
    "हिन्दी (Hindi)": "hi",
    "తెలుగు (Telugu)": "te",
}

LOCALE_MAP = {
    "en": "en_IN",
    "hi": "hi_IN",
    "te": "te_IN",
}


def load_locale(lang: str) -> dict:
    """Load and cache locale strings from JSON file."""
    if lang not in _cache:
        path = os.path.join(
            os.path.dirname(__file__), "locales", f"{lang}.json"
        )
        with open(path, encoding="utf-8") as f:
            _cache[lang] = json.load(f)
    return _cache[lang]


def t(key: str, lang: str, **kwargs) -> str:
    """Translate a key to the given language. Supports {var} interpolation."""
    strings = load_locale(lang)
    text = strings.get(key, key)
    if isinstance(text, list):
        return text
    return text.format(**kwargs) if kwargs else text


def fmt_currency(amount: float, lang: str) -> str:
    """Format amount as Indian Rupee in the given locale."""
    locale = LOCALE_MAP.get(lang, "en_IN")
    try:
        return format_currency(amount, "INR", locale=locale, format=u"¤#,##,##0")
    except Exception:
        return f"₹{amount:,.0f}"


def fmt_lakh_crore(amount: float, lang: str) -> str:
    """Express large amounts in lakh/crore notation per language."""
    labels = {
        "en": ("L", "Cr"),
        "hi": ("लाख", "करोड़"),
        "te": ("లక్ష", "కోటి"),
    }
    l_label, c_label = labels.get(lang, labels["en"])
    if amount >= 1_00_00_000:
        return f"₹{amount / 1_00_00_000:.2f} {c_label}"
    elif amount >= 1_00_000:
        return f"₹{amount / 1_00_000:.2f} {l_label}"
    return fmt_currency(amount, lang)


def fmt_date(d, lang: str) -> str:
    """Format a date object in the locale-appropriate format."""
    if isinstance(d, str):
        d = datetime.strptime(d, "%Y-%m-%d").date()
    locale = LOCALE_MAP.get(lang, "en_IN")
    try:
        return format_date(d, format="d MMM yyyy", locale=locale)
    except Exception:
        return d.strftime("%d %b %Y")


def get_categories(lang: str) -> list:
    """Return translated category list."""
    return t("categories", lang)


def category_map(lang: str) -> dict:
    """Map translated category names back to English keys."""
    en_cats = load_locale("en")["categories"]
    lang_cats = get_categories(lang)
    return dict(zip(lang_cats, en_cats))


def reverse_category_map(lang: str) -> dict:
    """Map English category keys to translated names."""
    en_cats = load_locale("en")["categories"]
    lang_cats = get_categories(lang)
    return dict(zip(en_cats, lang_cats))
