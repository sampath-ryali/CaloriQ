"""Structured QA response returned by the backend."""

from __future__ import annotations

from dataclasses import dataclass, asdict, field


@dataclass(slots=True)
class QaResponse:
    """Answer payload for nutrition label questions."""

    answer: str
    confidence: float
    insights: list[str] = field(default_factory=list)
    detected_intent: str = "general"
    source: str = "rule_based"
    health_score: int | None = None
    health_label: str | None = None
    diet_recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
