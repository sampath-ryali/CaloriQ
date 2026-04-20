"""OCR output model."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(slots=True)
class OcrResult:
    """Represents OCR output for a nutrition label image."""

    image_id: str
    raw_text: str
    clean_text: str
    source: str
    confidence: float

    def to_dict(self) -> dict[str, str | float]:
        return asdict(self)
