"""Structured nutrition data extracted from OCR text."""

from __future__ import annotations

from dataclasses import dataclass, asdict, field


@dataclass(slots=True)
class NutritionProfile:
    """Parsed nutrition facts and ingredient information."""

    calories: int | None = None
    sugar_g: float | None = None
    fat_g: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    sodium_mg: float | None = None
    fiber_g: float | None = None
    ingredients: list[str] = field(default_factory=list)
    raw_text: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
