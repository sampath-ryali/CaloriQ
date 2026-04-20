"""Image preprocessing utilities for nutrition label OCR."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from config import IMAGE_DIR
from models.preprocessed_image import PreprocessedImage
from services.image_service import get_image_path, ImageServiceError


PROCESSED_SUFFIX = "_processed"


class PreprocessingError(Exception):
    """Raised when preprocessing fails."""


def _load_cv2_and_numpy() -> tuple[Any, Any]:
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise PreprocessingError("OpenCV and numpy are required for image preprocessing") from exc
    return cv2, np


def load_image(image_path: Path) -> Any:
    """Load an image from disk into a BGR numpy array."""

    if not image_path.exists():
        raise PreprocessingError("Image file does not exist")

    cv2, np = _load_cv2_and_numpy()
    image_bytes = image_path.read_bytes()
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise PreprocessingError("Unable to decode the image")
    return image


def resize_image(image: Any, max_width: int = 1600, max_height: int = 1600) -> Any:
    """Resize an image while preserving its aspect ratio."""

    cv2, _ = _load_cv2_and_numpy()
    height, width = image.shape[:2]
    if width <= max_width and height <= max_height:
        return image

    scale = min(max_width / width, max_height / height)
    new_width = max(1, int(width * scale))
    new_height = max(1, int(height * scale))
    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)


def convert_to_grayscale(image: Any) -> Any:
    """Convert an image to grayscale."""

    cv2, _ = _load_cv2_and_numpy()
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def denoise_image(image: Any) -> Any:
    """Apply denoising to improve OCR readability."""

    cv2, _ = _load_cv2_and_numpy()
    if len(image.shape) == 2:
        return cv2.fastNlMeansDenoising(image, None, h=12, templateWindowSize=7, searchWindowSize=21)
    return cv2.fastNlMeansDenoisingColored(image, None, h=10, hColor=10, templateWindowSize=7, searchWindowSize=21)


def preprocess_image(image_id: str, max_width: int = 1600, max_height: int = 1600) -> PreprocessedImage:
    """Run resize, grayscale conversion, and denoising for a stored image."""

    try:
        original_path = get_image_path(image_id)
    except ImageServiceError as exc:
        raise PreprocessingError(str(exc)) from exc

    image = load_image(original_path)
    resized = resize_image(image, max_width=max_width, max_height=max_height)
    grayscale = convert_to_grayscale(resized)
    denoised = denoise_image(grayscale)

    cv2, _ = _load_cv2_and_numpy()
    processed_path = original_path.with_name(f"{original_path.stem}{PROCESSED_SUFFIX}{original_path.suffix}")
    cv2.imwrite(str(processed_path), denoised)

    processed_height, processed_width = denoised.shape[:2]
    return PreprocessedImage(
        source_image_id=image_id,
        processed_path=str(processed_path),
        width=processed_width,
        height=processed_height,
    )
