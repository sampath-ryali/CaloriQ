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
    serving_match = re.search(r"serving\s+size\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g", normalized, flags=re.IGNORECASE)
    serving_size_g = float(serving_match.group(1)) if serving_match else None

    def _extract_pair(label_pattern: str, unit: str) -> tuple[float | None, float | None]:
        pair_match = re.search(
            rf"\b(?:{label_pattern})\b\s*(?:[:\-])?\s*(\d+(?:\.\d+)?)\s*{unit}\s*(\d+(?:\.\d+)?)\s*{unit}",
            normalized,
            flags=re.IGNORECASE,
        )
        if pair_match:
            return float(pair_match.group(1)), float(pair_match.group(2))

        single_match = re.search(
            rf"\b(?:{label_pattern})\b\s*(?:[:\-])?\s*(\d+(?:\.\d+)?)\s*{unit}",
            normalized,
            flags=re.IGNORECASE,
        )
        if single_match:
            value = float(single_match.group(1))
            ratio = serving_size_g / 100.0 if serving_size_g else None
            if ratio and ratio > 0:
                pattern = rf"(\d+(?:\.\d+)?)\s*{unit}\b"
                all_numbers = [float(x) for x in re.findall(pattern, normalized, flags=re.IGNORECASE)]
                all_numbers += [float(x) for x in re.findall(r"\b(\d+(?:\.\d+)?)\b", normalized)]

                target_100g = value / ratio
                target_serving = value * ratio

                def find_close(target: float) -> float | None:
                    for num in all_numbers:
                        if abs(num - target) < 1e-4 or (target > 0 and abs(num - target) / target < 0.05):
                            return num
                    return None

                found_100g = find_close(target_100g)
                found_serving = find_close(target_serving)

                if found_100g is not None:
                    return found_100g, value
                elif found_serving is not None:
                    return value, found_serving

            return value, None

        return None, None

    calories_per_100g, calories_per_serving = _extract_pair(r"energy|calories?", "kcal")
    if calories_per_100g is None and calories_per_serving is None:
        calories_per_100g, calories_per_serving = _extract_pair(r"energy|calories?", "cal")

    calories_float = _to_float_or_none(extracted.get("calories"))
    calories = int(calories_per_serving or calories_float) if (calories_per_serving or calories_float) is not None else None

    if calories_per_serving is None and calories is not None:
        calories_per_serving = float(calories)
    if calories_per_100g is None and calories is not None and serving_size_g:
        calories_per_100g = float(calories)

    ingredients = _extract_ingredients(normalized)

    sugar_per_100g_g, sugar_per_serving_g = _extract_pair(r"total\s+sugars?|sugars?", "g")
    sugar_added_per_100g_g, sugar_added_per_serving_g = _extract_pair(r"added\s+sugars?|added\s+sugar", "g")
    fat_per_100g_g, fat_per_serving_g = _extract_pair(r"total\s+fat|fat", "g")
    saturated_fat_per_100g_g, saturated_fat_per_serving_g = _extract_pair(r"saturated\s+fat|sat\.?\s*fat", "g")
    trans_fat_per_100g_g, trans_fat_per_serving_g = _extract_pair(r"trans\s+fat", "g")
    protein_per_100g_g, protein_per_serving_g = _extract_pair(r"protein", "g")
    carbs_per_100g_g, carbs_per_serving_g = _extract_pair(r"carbohydrate|carbs?", "g")
    sodium_per_100g_mg, sodium_per_serving_mg = _extract_pair(r"sodium", "mg")
    fiber_per_100g_g, fiber_per_serving_g = _extract_pair(r"dietary\s+fiber|fiber", "g")
    cholesterol_per_100g_mg, cholesterol_per_serving_mg = _extract_pair(r"cholesterol", "mg")
    calcium_per_100g_mg, calcium_per_serving_mg = _extract_pair(r"calcium", "mg")
    potassium_per_100g_mg, potassium_per_serving_mg = _extract_pair(r"potassium", "mg")
    iron_per_100g_mg, iron_per_serving_mg = _extract_pair(r"iron", "mg")

    return NutritionProfile(
        calories=calories,
        calories_per_serving=calories_per_serving,
        calories_per_100g=calories_per_100g,
        serving_size_g=serving_size_g,
        sugar_g=_to_float_or_none(extracted.get("sugar")),
        sugar_per_serving_g=sugar_per_serving_g,
        sugar_per_100g_g=sugar_per_100g_g,
        sugar_added_g=_to_float_or_none(extracted.get("sugar_added")),
        sugar_added_per_serving_g=sugar_added_per_serving_g,
        sugar_added_per_100g_g=sugar_added_per_100g_g,
        fat_g=_to_float_or_none(extracted.get("fat")),
        fat_per_serving_g=fat_per_serving_g,
        fat_per_100g_g=fat_per_100g_g,
        saturated_fat_g=_to_float_or_none(extracted.get("saturated_fat")),
        saturated_fat_per_serving_g=saturated_fat_per_serving_g,
        saturated_fat_per_100g_g=saturated_fat_per_100g_g,
        trans_fat_g=_to_float_or_none(extracted.get("trans_fat")),
        trans_fat_per_serving_g=trans_fat_per_serving_g,
        trans_fat_per_100g_g=trans_fat_per_100g_g,
        protein_g=_to_float_or_none(extracted.get("protein")),
        protein_per_serving_g=protein_per_serving_g,
        protein_per_100g_g=protein_per_100g_g,
        carbs_g=_to_float_or_none(extracted.get("carbs")),
        carbs_per_serving_g=carbs_per_serving_g,
        carbs_per_100g_g=carbs_per_100g_g,
        sodium_mg=_to_float_or_none(extracted.get("sodium")),
        sodium_per_serving_mg=sodium_per_serving_mg,
        sodium_per_100g_mg=sodium_per_100g_mg,
        fiber_g=_to_float_or_none(extracted.get("fiber")),
        fiber_per_serving_g=fiber_per_serving_g,
        fiber_per_100g_g=fiber_per_100g_g,
        cholesterol_mg=_to_float_or_none(extracted.get("cholesterol")),
        cholesterol_per_serving_mg=cholesterol_per_serving_mg,
        cholesterol_per_100g_mg=cholesterol_per_100g_mg,
        calcium_mg=_to_float_or_none(extracted.get("calcium")),
        calcium_per_serving_mg=calcium_per_serving_mg,
        calcium_per_100g_mg=calcium_per_100g_mg,
        potassium_mg=_to_float_or_none(extracted.get("potassium")),
        potassium_per_serving_mg=potassium_per_serving_mg,
        potassium_per_100g_mg=potassium_per_100g_mg,
        iron_mg=_to_float_or_none(extracted.get("iron")),
        iron_per_serving_mg=iron_per_serving_mg,
        iron_per_100g_mg=iron_per_100g_mg,
        ingredients=ingredients,
        raw_text=normalized,
    )
