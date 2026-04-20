"""Local image storage service for uploaded label images."""

from __future__ import annotations

import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from config import IMAGE_DIR
from models.image_record import ImageRecord
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


IMAGE_INDEX_FILE = IMAGE_DIR / "image_index.json"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class ImageServiceError(Exception):
    """Raised when image upload or lookup fails."""


def ensure_image_store() -> None:
    """Ensure the image directory and index file exist."""

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not IMAGE_INDEX_FILE.exists():
        IMAGE_INDEX_FILE.write_text("[]", encoding="utf-8")


def _load_index() -> list[dict[str, str | None]]:
    ensure_image_store()
    raw_data = IMAGE_INDEX_FILE.read_text(encoding="utf-8-sig")
    if not raw_data.strip():
        return []
    try:
        payload = json.loads(raw_data)
    except json.JSONDecodeError:
        # Recover from malformed legacy file content so uploads can proceed.
        _save_index([])
        return []

    if not isinstance(payload, list):
        _save_index([])
        return []

    return payload


def _save_index(records: list[dict[str, str | None]]) -> None:
    ensure_image_store()
    IMAGE_INDEX_FILE.write_text(json.dumps(records, indent=2), encoding="utf-8")


def _get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def _get_content_type(filename: str, fallback: str | None = None) -> str:
    guessed_type, _ = mimetypes.guess_type(filename)
    return guessed_type or fallback or "application/octet-stream"


def save_uploaded_image(file_storage: FileStorage, user_id: str | None = None) -> ImageRecord:
    """Persist an uploaded image locally and return its metadata record."""

    if file_storage is None or not file_storage.filename:
        raise ImageServiceError("An image file is required")

    filename = secure_filename(file_storage.filename)
    if not filename:
        raise ImageServiceError("Invalid image filename")

    extension = _get_extension(filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise ImageServiceError("Unsupported image format")

    image_id = uuid4().hex
    stored_filename = f"{image_id}{extension}"
    stored_path = IMAGE_DIR / stored_filename

    file_storage.save(stored_path)

    record = ImageRecord(
        image_id=image_id,
        filename=filename,
        stored_path=str(stored_path),
        uploaded_at=datetime.now(timezone.utc).isoformat(),
        content_type=_get_content_type(filename, file_storage.mimetype),
        user_id=user_id,
    )

    records = _load_index()
    records.append(record.to_dict())
    _save_index(records)
    return record


def get_image_record(image_id: str) -> ImageRecord | None:
    """Look up a stored image record by image id."""

    for record in _load_index():
        if record["image_id"] == image_id:
            return ImageRecord(**record)
    return None


def get_image_path(image_id: str) -> Path:
    """Resolve the stored path for an image id."""

    record = get_image_record(image_id)
    if record is None:
        raise ImageServiceError("Image not found")

    path = Path(record.stored_path)
    if not path.exists():
        raise ImageServiceError("Stored image file is missing")
    return path
