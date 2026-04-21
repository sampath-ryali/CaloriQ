"""OCR extraction utilities for nutrition label images."""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

from models.ocr_result import OcrResult
from services.preprocessing_service import PreprocessingError, preprocess_image


class OcrServiceError(Exception):
    """Raised when OCR extraction fails."""


_SUPPORTED_OCR_ENGINES = {"easyocr", "pytesseract", "paddleocr", "auto"}


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _clean_text(text: str) -> str:
    cleaned = text.replace("\x0c", " ")
    cleaned = re.sub(r"[^\w\s%./:,;()\-+]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _get_primary_ocr_engine() -> str:
    engine = os.getenv("OCR_PRIMARY_ENGINE", "easyocr").strip().lower()
    if engine == "tesseract":
        engine = "pytesseract"

    if engine not in _SUPPORTED_OCR_ENGINES:
        supported = ", ".join(sorted(_SUPPORTED_OCR_ENGINES))
        raise OcrServiceError(f"Unsupported OCR_PRIMARY_ENGINE '{engine}'. Supported values: {supported}")

    return engine


def _get_engine_order(primary_engine: str) -> list[str]:
    if primary_engine == "auto":
        return ["paddleocr", "easyocr", "pytesseract"]

    order = [primary_engine]
    for engine in ("paddleocr", "easyocr", "pytesseract"):
        if engine not in order:
            order.append(engine)

    return order


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


@lru_cache(maxsize=1)
def _get_paddleocr_reader():
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:  # pragma: no cover - import guard
        raise OcrServiceError("PaddleOCR is not installed") from exc

    use_gpu = os.getenv("OCR_USE_GPU", "false").strip().lower() == "true"
    device = "gpu" if use_gpu else "cpu"
    language = os.getenv("OCR_PADDLE_LANG", "en").strip() or "en"

    init_attempts = [
        {"use_angle_cls": True, "lang": language, "device": device},
        {"use_angle_cls": True, "lang": language, "use_gpu": use_gpu},
        {"lang": language},
    ]

    last_error: Exception | None = None
    for kwargs in init_attempts:
        try:
            return PaddleOCR(**kwargs)
        except Exception as exc:  # pragma: no cover - runtime guard
            last_error = exc
            continue

    raise OcrServiceError(f"Failed to initialize PaddleOCR: {last_error}") from last_error


def _paddleocr_extract(image_path: Path) -> tuple[str, float]:
    reader = _get_paddleocr_reader()

    try:
        result = reader.ocr(str(image_path), cls=True)
    except TypeError:
        try:
            result = reader.ocr(str(image_path))
        except Exception as exc:  # pragma: no cover - runtime guard
            raise OcrServiceError(f"PaddleOCR inference failed: {exc}") from exc
    except Exception as exc:  # pragma: no cover - runtime guard
        # PaddleOCR v3 may expose predict() instead of legacy ocr() semantics.
        if hasattr(reader, "predict"):
            try:
                result = reader.predict(str(image_path))
            except Exception as inner_exc:  # pragma: no cover - runtime guard
                raise OcrServiceError(f"PaddleOCR inference failed: {inner_exc}") from inner_exc
        else:
            raise OcrServiceError(f"PaddleOCR inference failed: {exc}") from exc

    texts: list[str] = []
    confidences: list[float] = []

    for block in result or []:
        if not block:
            continue
        for line in block:
            if not isinstance(line, (list, tuple)) or len(line) < 2:
                continue

            recognition = line[1]
            if not isinstance(recognition, (list, tuple)) or len(recognition) < 2:
                continue

            text = str(recognition[0]).strip()
            if text:
                texts.append(text)

            try:
                confidences.append(float(recognition[1]))
            except (TypeError, ValueError):
                continue

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


def _run_engine(engine: str, image_path: Path) -> tuple[str, float]:
    if engine == "paddleocr":
        return _paddleocr_extract(image_path)
    if engine == "easyocr":
        return _easyocr_extract(image_path)
    if engine == "pytesseract":
        return _pytesseract_extract(image_path)

    raise OcrServiceError(f"Unsupported OCR engine '{engine}'")


def extract_text_from_path(image_path: Path) -> OcrResult:
    """Run OCR on a preprocessed image path and return normalized text."""

    if not image_path.exists():
        raise OcrServiceError("OCR input image not found")

    raw_text = ""
    confidence = 0.0
    source = ""

    primary_engine = _get_primary_ocr_engine()
    engine_order = _get_engine_order(primary_engine)
    failures: list[str] = []

    for engine in engine_order:
        try:
            raw_text, confidence = _run_engine(engine, image_path)
            source = engine
            break
        except OcrServiceError as exc:
            failures.append(f"{engine}: {exc}")

    if not source:
        details = " | ".join(failures) if failures else "No engine attempts were made"
        raise OcrServiceError(f"All OCR engines failed. {details}")

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
