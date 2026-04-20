"""Dictionary-based multilingual support for response localization."""

from __future__ import annotations


SUPPORTED_LANGUAGES = {"en", "es"}

TEXT_MAP = {
    "The label indicates about": {
        "es": "La etiqueta indica aproximadamente",
    },
    "calories.": {
        "es": "calorias.",
    },
    "g of sugar.": {
        "es": "g de azucar.",
    },
    "g of fat.": {
        "es": "g de grasa.",
    },
    "g of protein.": {
        "es": "g de proteina.",
    },
    "The ingredients listed are:": {
        "es": "Los ingredientes listados son:",
    },
    "Potential allergens detected:": {
        "es": "Alergenos potenciales detectados:",
    },
    "No common allergens were detected from the parsed ingredient list.": {
        "es": "No se detectaron alergenos comunes en la lista de ingredientes analizada.",
    },
    "I could not determine": {
        "es": "No pude determinar",
    },
    "from the label text.": {
        "es": "a partir del texto de la etiqueta.",
    },
    "high sugar content": {
        "es": "alto contenido de azucar",
    },
    "low sugar content": {
        "es": "bajo contenido de azucar",
    },
    "low fat product": {
        "es": "producto bajo en grasa",
    },
    "high protein content": {
        "es": "alto contenido de proteina",
    },
    "high calorie product": {
        "es": "producto alto en calorias",
    },
    "low calorie product": {
        "es": "producto bajo en calorias",
    },
    "possible allergens detected": {
        "es": "posibles alergenos detectados",
    },
    "detected allergens": {
        "es": "alergenos detectados",
    },
    "no targeted allergen keywords detected": {
        "es": "no se detectaron palabras clave del alergeno objetivo",
    },
    "source": {
        "es": "fuente",
    },
}


def normalize_language(language: str | None) -> str:
    if not language:
        return "en"
    normalized = language.lower().strip()
    return normalized if normalized in SUPPORTED_LANGUAGES else "en"


def translate_text(text: str, language: str) -> str:
    target = normalize_language(language)
    if target == "en":
        return text

    translated = text
    for source, translations in TEXT_MAP.items():
        replacement = translations.get(target)
        if replacement:
            translated = translated.replace(source, replacement)
    return translated


def translate_list(items: list[str], language: str) -> list[str]:
    return [translate_text(item, language) for item in items]
