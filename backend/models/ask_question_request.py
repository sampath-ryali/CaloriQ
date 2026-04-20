"""Request payload for the question answering endpoint."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AskQuestionRequest:
    """Validated input for the ask-question API."""

    image_id: str
    question: str
    language: str = "en"
