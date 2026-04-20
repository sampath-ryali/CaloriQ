"""Regression tests for QA intent routing and nutrient extraction robustness."""

from __future__ import annotations

import unittest

from models.nutrition_profile import NutritionProfile
from services.advanced_inference import NutritionExtractor
from services.qa_engine import answer_question


class QaEngineIntentTests(unittest.TestCase):
    def test_fitness_goal_question_not_misrouted_to_fat_amount(self) -> None:
        profile = NutritionProfile(
            calories=110,
            sugar_g=1.0,
            fat_g=0.5,
            protein_g=3.0,
            carbs_g=23.0,
            sodium_mg=400.0,
            fiber_g=2.0,
            ingredients=[],
            raw_text="",
        )

        response = answer_question(profile, "is this better for muscle gain or fat loss based on these macros")

        self.assertEqual(response.detected_intent, "fitness_goal")
        self.assertIn("fat loss", response.answer.lower())
        self.assertNotIn("g of fat", response.answer.lower())

    def test_fat_amount_question_still_returns_fat_value(self) -> None:
        profile = NutritionProfile(
            calories=110,
            sugar_g=1.0,
            fat_g=0.5,
            protein_g=3.0,
            carbs_g=23.0,
            sodium_mg=400.0,
            fiber_g=2.0,
            ingredients=[],
            raw_text="",
        )

        response = answer_question(profile, "how much fat does this have")

        self.assertEqual(response.detected_intent, "fat")
        self.assertIn("0.5", response.answer)


class NutritionExtractorPatternTests(unittest.TestCase):
    def test_unitless_macro_value_is_not_treated_as_grams(self) -> None:
        extractor = NutritionExtractor()
        parsed = extractor.extract("Calories 110 Total Fat 390 Sodium 400mg")

        self.assertEqual(parsed["fat"], "Not found")
        self.assertEqual(parsed["sodium"], 400.0)

    def test_grams_value_is_still_parsed_for_fat(self) -> None:
        extractor = NutritionExtractor()
        parsed = extractor.extract("Calories 110 Total Fat 0.5g Sodium 400mg")

        self.assertEqual(parsed["fat"], 0.5)


if __name__ == "__main__":
    unittest.main()
