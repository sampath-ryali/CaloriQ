"""Integration-style tests for the analysis pipeline."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from models.ask_question_request import AskQuestionRequest
from models.ocr_result import OcrResult
from services.analysis_service import AnalysisService


class AnalysisServiceIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ocr_text = (
            "Nutrition Information "
            "Servings per package: 10 "
            "Serving size: 30 g (Approx. 3 biscuits) "
            "Per 100 g Per Serving (30 g) "
            "Energy 480 kcal 144 kcal "
            "Protein 6.5 g 2.0 g "
            "Carbohydrate 68 g 20.4 g "
            "- Total Sugars 28 g 8.4 g "
            "Total Fat 20 g 6 g "
            "- Saturated Fat 9 g 2.7 g "
            "- Trans Fat 0.2 g 0.06 g "
            "Cholesterol 5 mg 1.5 mg "
            "Sodium 320 mg 96 mg "
            "Dietary Fiber 3.5 g 1.05 g"
        )

    def test_analyze_returns_per_serving_energy(self) -> None:
        request = AskQuestionRequest(
            image_id="sample-image",
            question="total energy?",
            language="en",
        )
        ocr = OcrResult(
            image_id="sample-image",
            raw_text=self.ocr_text,
            clean_text=self.ocr_text,
            source="easyocr",
            confidence=0.92,
        )

        with patch("services.analysis_service.extract_text_from_image_id", return_value=ocr):
            result = AnalysisService.analyze(request)

        self.assertEqual(result.source, "rule_based")
        self.assertIn("144", result.answer)
        self.assertIn("480", result.answer)

    def test_analyze_returns_total_sugar_from_label(self) -> None:
        request = AskQuestionRequest(
            image_id="sample-image",
            question="total sugar?",
            language="en",
        )
        ocr = OcrResult(
            image_id="sample-image",
            raw_text=self.ocr_text,
            clean_text=self.ocr_text,
            source="easyocr",
            confidence=0.92,
        )

        with patch("services.analysis_service.extract_text_from_image_id", return_value=ocr):
            result = AnalysisService.analyze(request)

        self.assertEqual(result.source, "rule_based")
        self.assertIn("8.4", result.answer)
        self.assertIn("28", result.answer)

    def test_analyze_still_uses_rule_engine_for_health_questions(self) -> None:
        request = AskQuestionRequest(
            image_id="sample-image",
            question="How healthy is this product?",
            language="en",
        )
        ocr = OcrResult(
            image_id="sample-image",
            raw_text=self.ocr_text,
            clean_text=self.ocr_text,
            source="easyocr",
            confidence=0.92,
        )

        with patch("services.analysis_service.extract_text_from_image_id", return_value=ocr), patch(
            "services.qa_engine.QwenModel.call", side_effect=RuntimeError("Ollama unavailable")
        ), patch.dict("os.environ", {"QWEN_STRICT": "false", "ENABLE_LLM": "false", "ENABLE_QWEN": "true", "LLM_PROVIDER": "qwen"}):
            result = AnalysisService.analyze(request)

        self.assertEqual(result.source, "rule_based")
        self.assertIsNotNone(result.health_score)
        self.assertTrue(len(result.diet_recommendations) > 0)
        self.assertTrue(result.answer)


if __name__ == "__main__":
    unittest.main()