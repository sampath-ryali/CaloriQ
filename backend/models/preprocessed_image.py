"""Metadata for a preprocessed image artifact."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(slots=True)
class PreprocessedImage:
    """Represents a normalized image generated from the original upload."""

    source_image_id: str
    processed_path: str
    width: int
    height: int
    grayscale: bool = True
    denoised: bool = True

    def to_dict(self) -> dict[str, str | int | bool]:
        return asdict(self)
