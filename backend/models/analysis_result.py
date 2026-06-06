"""Combined analysis result returned by the question answering pipeline."""

from __future__ import annotations

from dataclasses import dataclass, asdict, field


@dataclass(slots=True)
class AnalysisResult:
    """End-to-end pipeline result for one nutrition label question."""

    image_id: str
    question: str
    answer: str
    confidence: float
    insights: list[str] = field(default_factory=list)
    question_type: str = "extraction"
    detected_intent: str = "general"
    source: str = "rule_based"
    health_score: int | None = None
    health_label: str | None = None
    diet_recommendations: list[str] = field(default_factory=list)
    language: str = "en"
    ocr_text: str = ""
    nutrition: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
