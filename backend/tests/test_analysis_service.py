"""Integration-style tests for the analysis pipeline."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from models.ask_question_request import AskQuestionRequest
from models.ocr_result import OcrResult
from services.analysis_service import AnalysisService


class AnalysisServiceIntegrationTests(unittest.TestCase):
    def test_analyze_falls_back_to_rule_engine_when_qwen_unavailable(self) -> None:
        request = AskQuestionRequest(
            image_id="sample-image",
            question="How healthy is this product?",
            language="en",
        )
        ocr = OcrResult(
            image_id="sample-image",
            raw_text="Calories 180 Protein 12g Fat 7g Carbs 18g Sodium 180mg Sugar 5g",
            clean_text="Calories 180 Protein 12g Fat 7g Carbs 18g Sodium 180mg Sugar 5g",
            source="easyocr",
            confidence=0.92,
        )

        with patch("services.analysis_service.extract_text_from_image_id", return_value=ocr), patch(
            "services.qa_engine.QwenModel.call", side_effect=RuntimeError("Ollama unavailable")
        ):
            result = AnalysisService.analyze(request)

        self.assertEqual(result.source, "rule_based")
        self.assertIsNotNone(result.health_score)
        self.assertTrue(len(result.diet_recommendations) > 0)
        self.assertTrue(result.answer)


if __name__ == "__main__":
    unittest.main()