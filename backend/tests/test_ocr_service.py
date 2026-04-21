"""Unit tests for OCR engine selection and fallback."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.ocr_service import OcrServiceError, extract_text_from_path


class OcrServiceEngineSelectionTests(unittest.TestCase):
    def _temp_image_path(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "sample_processed.png"
        path.write_bytes(b"fake-image")
        return path

    def test_uses_easyocr_by_default(self) -> None:
        image_path = self._temp_image_path()

        with patch.dict(os.environ, {"OCR_PRIMARY_ENGINE": "easyocr"}, clear=False), patch(
            "services.ocr_service._easyocr_extract",
            return_value=("Calories 120", 0.9),
        ) as easy_mock, patch(
            "services.ocr_service._paddleocr_extract",
            side_effect=AssertionError("paddle should not be called when easyocr succeeds"),
        ), patch(
            "services.ocr_service._pytesseract_extract",
            side_effect=AssertionError("pytesseract should not be called"),
        ):
            result = extract_text_from_path(image_path)

        self.assertEqual(result.source, "easyocr")
        self.assertEqual(result.clean_text, "Calories 120")
        easy_mock.assert_called_once()

    def test_uses_paddle_as_primary_when_configured(self) -> None:
        image_path = self._temp_image_path()

        with patch.dict(os.environ, {"OCR_PRIMARY_ENGINE": "paddleocr"}, clear=False), patch(
            "services.ocr_service._paddleocr_extract",
            return_value=("Protein 10g", 0.88),
        ) as paddle_mock, patch(
            "services.ocr_service._easyocr_extract",
            side_effect=AssertionError("easyocr should not run when paddle succeeds"),
        ):
            result = extract_text_from_path(image_path)

        self.assertEqual(result.source, "paddleocr")
        self.assertEqual(result.clean_text, "Protein 10g")
        paddle_mock.assert_called_once()

    def test_falls_back_from_paddle_to_easyocr(self) -> None:
        image_path = self._temp_image_path()

        with patch.dict(os.environ, {"OCR_PRIMARY_ENGINE": "paddleocr"}, clear=False), patch(
            "services.ocr_service._paddleocr_extract",
            side_effect=OcrServiceError("paddle unavailable"),
        ), patch(
            "services.ocr_service._easyocr_extract",
            return_value=("Fat 5g", 0.81),
        ) as easy_mock:
            result = extract_text_from_path(image_path)

        self.assertEqual(result.source, "easyocr")
        self.assertEqual(result.clean_text, "Fat 5g")
        easy_mock.assert_called_once()

    def test_invalid_primary_engine_raises(self) -> None:
        image_path = self._temp_image_path()

        with patch.dict(os.environ, {"OCR_PRIMARY_ENGINE": "invalid_engine"}, clear=False):
            with self.assertRaises(OcrServiceError):
                extract_text_from_path(image_path)


if __name__ == "__main__":
    unittest.main()
