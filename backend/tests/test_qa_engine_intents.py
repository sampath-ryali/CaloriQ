"""Regression tests for QA intent routing and nutrient extraction robustness."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from models.nutrition_profile import NutritionProfile
from services.advanced_inference import NutritionExtractor
from services.qa_engine import answer_question


class QaEngineIntentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env_patcher = patch.dict("os.environ", {"ENABLE_QWEN": "false", "ENABLE_LLM": "false"})
        self.env_patcher.start()

    def tearDown(self) -> None:
        self.env_patcher.stop()

    def test_sugar_free_question_is_reasoning_not_extraction(self) -> None:
        profile = NutritionProfile(
            calories=120,
            sugar_g=5.0,
            fat_g=5.0,
            protein_g=10.0,
            carbs_g=18.0,
            sodium_mg=180.0,
            fiber_g=2.0,
            ingredients=[],
            raw_text="",
        )

        response = answer_question(profile, "is it sugar free?")

        self.assertEqual(response.question_type, "reasoning")
        self.assertEqual(response.detected_intent, "sugar_status")
        self.assertIn("not sugar free", response.answer.lower())
        self.assertNotEqual(response.answer.strip(), "0g")

    def test_sugar_amount_question_stays_extraction(self) -> None:
        profile = NutritionProfile(
            calories=120,
            sugar_g=5.0,
            fat_g=5.0,
            protein_g=10.0,
            carbs_g=18.0,
            sodium_mg=180.0,
            fiber_g=2.0,
            ingredients=[],
            raw_text="",
        )

        response = answer_question(profile, "how much sugar is there?")

        self.assertEqual(response.question_type, "extraction")
        self.assertEqual(response.detected_intent, "sugar")
        self.assertIn("5", response.answer)

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

    def test_bare_nutrient_prompt_is_extraction(self) -> None:
        profile = NutritionProfile(
            calories=120,
            sugar_g=0.0,
            fat_g=3.0,
            protein_g=3.8,
            carbs_g=5.3,
            sodium_mg=58.0,
            fiber_g=0.0,
            ingredients=[],
            raw_text="",
        )

        response = answer_question(profile, "sodium?")

        self.assertEqual(response.question_type, "extraction")
        self.assertEqual(response.detected_intent, "sodium")
        self.assertIn("58", response.answer)

    def test_nutrient_summary_includes_cholesterol_and_calcium(self) -> None:
        profile = NutritionProfile(
            calories=63.4,
            protein_g=3.8,
            fat_g=3.0,
            saturated_fat_g=1.8,
            trans_fat_g=0.0,
            carbs_g=5.3,
            sugar_g=0.0,
            sodium_mg=58.0,
            fiber_g=None,
            cholesterol_mg=15.0,
            calcium_mg=106.0,
            potassium_mg=120.0,
            iron_mg=2.0,
            ingredients=[],
            raw_text="",
        )

        response = answer_question(profile, "what nutrients are there in this product?")

        self.assertEqual(response.question_type, "extraction")
        self.assertEqual(response.detected_intent, "nutrient_summary")
        self.assertIn("Cholesterol", response.answer)
        self.assertIn("Calcium", response.answer)
        self.assertIn("Iron", response.answer)

    def test_cholesterol_question_is_extraction(self) -> None:
        profile = NutritionProfile(
            calories=63.4,
            cholesterol_mg=15.0,
            calcium_mg=106.0,
            ingredients=[],
            raw_text="",
        )

        response = answer_question(profile, "cholesterol?")

        self.assertEqual(response.question_type, "extraction")
        self.assertEqual(response.detected_intent, "cholesterol")
        self.assertIn("15", response.answer)

    def test_calcium_question_is_extraction(self) -> None:
        profile = NutritionProfile(
            calories=63.4,
            cholesterol_mg=15.0,
            calcium_mg=106.0,
            ingredients=[],
            raw_text="",
        )

        response = answer_question(profile, "calcium?")

        self.assertEqual(response.question_type, "extraction")
        self.assertEqual(response.detected_intent, "calcium")
        self.assertIn("106", response.answer)


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
