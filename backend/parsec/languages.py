"""Authoritative language registry for Parsec OCR.

Maps PaddleOCR short codes to display names, Tesseract codes, and script
groups. Derived from the ocrmypdf_paddleocr plugin's lang_map.py (49 entries).

Usage:
    from parsec.languages import get_tesseract_code, get_language, all_languages

    tess = get_tesseract_code("en")      # "eng"
    lang = get_language("ko")            # raises ValueError — use "korean"
    langs = all_languages()              # list of dicts for JSON serialization
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    """A supported OCR language.

    Attributes:
        display_name: Human-readable name (e.g. "English").
        short_code: PaddleOCR code used throughout the system (e.g. "en", "ch", "korean").
        tesseract_code: Tesseract ISO 639-2 code (e.g. "eng", "chi_sim", "kor").
        script_group: Writing system family (e.g. "Latin", "CJK", "Arabic").
    """

    display_name: str
    short_code: str
    tesseract_code: str
    script_group: str


# All 49 languages supported by the ocrmypdf_paddleocr plugin.
# English is first (system default). Remaining grouped by script, then alphabetical.
LANGUAGES: list[Language] = [
    # --- Latin script ---
    Language("English", "en", "eng", "Latin"),
    Language("French", "french", "fra", "Latin"),
    Language("German", "german", "deu", "Latin"),
    Language("Spanish", "es", "spa", "Latin"),
    Language("Portuguese", "pt", "por", "Latin"),
    Language("Italian", "it", "ita", "Latin"),
    Language("Dutch", "nl", "nld", "Latin"),
    Language("Norwegian", "no", "nor", "Latin"),
    Language("Swedish", "sv", "swe", "Latin"),
    Language("Danish", "da", "dan", "Latin"),
    Language("Finnish", "fi", "fin", "Latin"),
    Language("Polish", "pl", "pol", "Latin"),
    Language("Czech", "cs", "ces", "Latin"),
    Language("Slovak", "sk", "slk", "Latin"),
    Language("Slovenian", "sl", "slv", "Latin"),
    Language("Croatian", "hr", "hrv", "Latin"),
    Language("Romanian", "ro", "ron", "Latin"),
    Language("Hungarian", "hu", "hun", "Latin"),
    Language("Turkish", "tr", "tur", "Latin"),
    Language("Estonian", "et", "est", "Latin"),
    Language("Latvian", "lv", "lav", "Latin"),
    Language("Lithuanian", "lt", "lit", "Latin"),
    Language("Indonesian", "id", "ind", "Latin"),
    Language("Malay", "ms", "msa", "Latin"),
    Language("Vietnamese", "vi", "vie", "Latin"),
    Language("Latin", "la", "lat", "Latin"),
    # --- CJK ---
    Language("Chinese (Simplified)", "ch", "chi_sim", "CJK"),
    Language("Chinese (Traditional)", "chinese_cht", "chi_tra", "CJK"),
    Language("Japanese", "japan", "jpn", "CJK"),
    Language("Korean", "korean", "kor", "CJK"),
    # --- Cyrillic ---
    Language("Russian", "ru", "rus", "Cyrillic"),
    Language("Ukrainian", "uk", "ukr", "Cyrillic"),
    Language("Bulgarian", "bg", "bul", "Cyrillic"),
    # --- Arabic ---
    Language("Arabic", "ar", "ara", "Arabic"),
    Language("Persian", "fa", "fas", "Arabic"),
    Language("Urdu", "ur", "urd", "Arabic"),
    # --- Devanagari / Indic ---
    Language("Hindi", "hi", "hin", "Devanagari"),
    Language("Marathi", "mr", "mar", "Devanagari"),
    Language("Nepali", "ne", "nep", "Devanagari"),
    Language("Bengali", "bn", "ben", "Bengali"),
    Language("Tamil", "ta", "tam", "Tamil"),
    Language("Telugu", "te", "tel", "Telugu"),
    Language("Kannada", "ka", "kan", "Kannada"),
    # --- Greek / Hebrew ---
    Language("Greek", "el", "ell", "Greek"),
    Language("Hebrew", "he", "heb", "Hebrew"),
    # --- Southeast Asian ---
    Language("Thai", "th", "tha", "Thai"),
    Language("Myanmar (Burmese)", "my", "mya", "Myanmar"),
    Language("Khmer", "km", "khm", "Khmer"),
    Language("Lao", "lo", "lao", "Lao"),
]

# --- Lookup indexes (built once at import time) ---

_BY_SHORT_CODE: dict[str, Language] = {lang.short_code: lang for lang in LANGUAGES}
_SHORT_TO_TESSERACT: dict[str, str] = {lang.short_code: lang.tesseract_code for lang in LANGUAGES}


def get_language(short_code: str) -> Language:
    """Look up a Language by its short code.

    Args:
        short_code: PaddleOCR language code (e.g. "en", "ch", "korean").

    Returns:
        The matching Language dataclass.

    Raises:
        ValueError: If the short code is not in the registry.
    """
    lang = _BY_SHORT_CODE.get(short_code)
    if lang is None:
        raise ValueError(
            f"Unsupported language: {short_code!r}. "
            f"Use all_languages() to see valid codes."
        )
    return lang


def get_tesseract_code(short_code: str) -> str:
    """Convert a PaddleOCR short code to the Tesseract ISO 639-2 code.

    Args:
        short_code: PaddleOCR language code (e.g. "en", "korean").

    Returns:
        Tesseract language code (e.g. "eng", "kor").

    Raises:
        ValueError: If the short code is not in the registry.
    """
    code = _SHORT_TO_TESSERACT.get(short_code)
    if code is None:
        raise ValueError(
            f"Unsupported language: {short_code!r}. "
            f"Use all_languages() to see valid codes."
        )
    return code


def all_languages() -> list[dict[str, str]]:
    """Return all supported languages as a list of dicts for JSON serialization.

    Each dict has keys: display_name, short_code, tesseract_code, script_group.
    English is always first.
    """
    return [
        {
            "display_name": lang.display_name,
            "short_code": lang.short_code,
            "tesseract_code": lang.tesseract_code,
            "script_group": lang.script_group,
        }
        for lang in LANGUAGES
    ]
