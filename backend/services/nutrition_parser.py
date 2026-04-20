"""Regex-based nutrition label parser."""

from __future__ import annotations

import re

from models.nutrition_profile import NutritionProfile
from services.advanced_inference import NutritionExtractor


class NutritionParserError(Exception):
    """Raised when nutrition parsing fails."""


_EXTRACTOR = NutritionExtractor()


def _to_float_or_none(value: object) -> float | None:
    if value is None or value == "Not found":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_ingredients(text: str) -> list[str]:
    ingredient_match = re.search(
        r"\bingredients?\s*[:\-]?\s*(.+?)(?:\bnutrition\b|\ballergen\b|\bcontains\b|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not ingredient_match:
        return []

    ingredient_text = ingredient_match.group(1)
    ingredient_text = re.sub(r"\s+", " ", ingredient_text).strip()
    ingredient_text = ingredient_text.rstrip(" .;")
    if not ingredient_text:
        return []

    parts = re.split(r",|;| and | with ", ingredient_text, flags=re.IGNORECASE)
    cleaned = [part.strip(" .;:-").lower() for part in parts if part.strip(" .;:-")]
    return cleaned


def parse_nutrition_text(text: str) -> NutritionProfile:
    """Convert OCR text into structured nutrition facts."""

    normalized = re.sub(r"\s+", " ", text or "").strip()
    if not normalized:
        raise NutritionParserError("OCR text is empty")

    extracted = _EXTRACTOR.extract(normalized)

    calories_float = _to_float_or_none(extracted.get("calories"))
    calories = int(calories_float) if calories_float is not None else None

    ingredients = _extract_ingredients(normalized)

    return NutritionProfile(
        calories=calories,
        sugar_g=_to_float_or_none(extracted.get("sugar")),
        fat_g=_to_float_or_none(extracted.get("fat")),
        protein_g=_to_float_or_none(extracted.get("protein")),
        carbs_g=_to_float_or_none(extracted.get("carbs")),
        sodium_mg=_to_float_or_none(extracted.get("sodium")),
        fiber_g=_to_float_or_none(extracted.get("fiber")),
        ingredients=ingredients,
        raw_text=normalized,
    )
