"""Image upload record model."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(slots=True)
class ImageRecord:
    """Metadata for an uploaded nutrition label image."""

    image_id: str
    filename: str
    stored_path: str
    uploaded_at: str
    content_type: str
    user_id: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)
