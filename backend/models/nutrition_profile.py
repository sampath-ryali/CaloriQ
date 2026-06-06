"""Structured nutrition data extracted from OCR text."""

from __future__ import annotations

from dataclasses import dataclass, asdict, field


@dataclass(slots=True)
class NutritionProfile:
    """Parsed nutrition facts and ingredient information."""

    calories: int | None = None
    calories_per_serving: int | None = None
    calories_per_100g: int | None = None
    serving_size_g: float | None = None
    sugar_g: float | None = None
    sugar_per_serving_g: float | None = None
    sugar_per_100g_g: float | None = None
    fat_g: float | None = None
    fat_per_serving_g: float | None = None
    fat_per_100g_g: float | None = None
    saturated_fat_g: float | None = None
    saturated_fat_per_serving_g: float | None = None
    saturated_fat_per_100g_g: float | None = None
    trans_fat_g: float | None = None
    trans_fat_per_serving_g: float | None = None
    trans_fat_per_100g_g: float | None = None
    protein_g: float | None = None
    protein_per_serving_g: float | None = None
    protein_per_100g_g: float | None = None
    carbs_g: float | None = None
    carbs_per_serving_g: float | None = None
    carbs_per_100g_g: float | None = None
    sodium_mg: float | None = None
    sodium_per_serving_mg: float | None = None
    sodium_per_100g_mg: float | None = None
    fiber_g: float | None = None
    fiber_per_serving_g: float | None = None
    fiber_per_100g_g: float | None = None
    sugar_added_g: float | None = None
    sugar_added_per_serving_g: float | None = None
    sugar_added_per_100g_g: float | None = None
    cholesterol_mg: float | None = None
    cholesterol_per_serving_mg: float | None = None
    cholesterol_per_100g_mg: float | None = None
    calcium_mg: float | None = None
    calcium_per_serving_mg: float | None = None
    calcium_per_100g_mg: float | None = None
    potassium_mg: float | None = None
    potassium_per_serving_mg: float | None = None
    potassium_per_100g_mg: float | None = None
    iron_mg: float | None = None
    iron_per_serving_mg: float | None = None
    iron_per_100g_mg: float | None = None
    ingredients: list[str] = field(default_factory=list)
    raw_text: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
