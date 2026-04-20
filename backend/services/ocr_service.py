"""OCR extraction utilities for nutrition label images."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from models.ocr_result import OcrResult
from services.preprocessing_service import PreprocessingError, preprocess_image


class OcrServiceError(Exception):
    """Raised when OCR extraction fails."""


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _clean_text(text: str) -> str:
    cleaned = text.replace("\x0c", " ")
    cleaned = re.sub(r"[^\w\s%./:,;()\-+]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


@lru_cache(maxsize=1)
def _get_easyocr_reader():
    try:
        import easyocr
    except ImportError as exc:  # pragma: no cover - import guard
        raise OcrServiceError("EasyOCR is not installed") from exc

    try:
        return easyocr.Reader(["en"], gpu=False)
    except Exception as exc:  # pragma: no cover - runtime guard
        raise OcrServiceError(f"Failed to initialize EasyOCR: {exc}") from exc


def _easyocr_extract(image_path: Path) -> tuple[str, float]:
    reader = _get_easyocr_reader()
    results = reader.readtext(str(image_path), detail=1, paragraph=False)
    texts: list[str] = []
    confidences: list[float] = []

    for detection in results:
        if len(detection) == 3:
            _, text, confidence = detection
        else:
            continue
        if text:
            texts.append(text)
            confidences.append(float(confidence))

    raw_text = " ".join(texts)
    average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return raw_text, average_confidence


def _pytesseract_extract(image_path: Path) -> tuple[str, float]:
    try:
        import cv2
        import pytesseract
    except ImportError as exc:  # pragma: no cover - import guard
        raise OcrServiceError("Neither EasyOCR nor pytesseract is available") from exc

    image = cv2.imread(str(image_path))
    if image is None:
        raise OcrServiceError("Unable to read image for OCR fallback")

    raw_text = pytesseract.image_to_string(image)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    confidences = [float(value) for value in data.get("conf", []) if str(value).isdigit() and int(value) >= 0]
    average_confidence = (sum(confidences) / len(confidences)) / 100.0 if confidences else 0.0
    return raw_text, average_confidence


def extract_text_from_path(image_path: Path) -> OcrResult:
    """Run OCR on a preprocessed image path and return normalized text."""

    if not image_path.exists():
        raise OcrServiceError("OCR input image not found")

    raw_text = ""
    confidence = 0.0
    source = "easyocr"

    try:
        raw_text, confidence = _easyocr_extract(image_path)
    except OcrServiceError:
        source = "pytesseract"
        raw_text, confidence = _pytesseract_extract(image_path)

    clean_text = _clean_text(raw_text)
    return OcrResult(
        image_id=image_path.stem.replace("_processed", ""),
        raw_text=_normalize_whitespace(raw_text),
        clean_text=clean_text,
        source=source,
        confidence=round(confidence, 4),
    )


def extract_text_from_image_id(image_id: str) -> OcrResult:
    """Preprocess an uploaded image, then extract OCR text."""

    try:
        processed = preprocess_image(image_id)
    except PreprocessingError as exc:
        raise OcrServiceError(str(exc)) from exc

    return extract_text_from_path(Path(processed.processed_path))
