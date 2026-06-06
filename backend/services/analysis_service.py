"""Orchestrates OCR, parsing, and question answering for nutrition labels."""

from __future__ import annotations

import os

from models.analysis_result import AnalysisResult
from models.ask_question_request import AskQuestionRequest
from services.i18n_service import normalize_language, translate_list, translate_text
from services.nutrition_parser import NutritionParserError, parse_nutrition_text
from services.ocr_service import OcrServiceError, extract_text_from_image_id
from services.qa_engine import QaEngineError, answer_question


class AnalysisServiceError(Exception):
    """Raised when the end-to-end analysis pipeline fails."""


class AnalysisService:
    """High-level service for answering nutrition label questions."""

    @staticmethod
    def _get_language_dictionary(language: str) -> dict[str, str]:
        dictionaries = {
            "en": {
                "analysis_failed": "I could not process the label right now.",
            },
            "es": {
                "analysis_failed": "No pude procesar la etiqueta en este momento.",
            },
        }
        return dictionaries.get(language, dictionaries["en"])

    @staticmethod
    def _attempt_vlm_answer(request: AskQuestionRequest, nutrition_text: str) -> tuple[str, float, str] | None:
        """Optional hook for a future VLM; returns None when unavailable."""

        if os.getenv("ENABLE_VLM", "false").lower() != "true":
            return None

        # Placeholder for a future BLIP/LLaVA integration.
        return None

    @staticmethod
    def analyze(request: AskQuestionRequest) -> AnalysisResult:
        """Run the complete pipeline and return a structured response."""

        language = normalize_language(request.language)
        try:
            ocr_result = extract_text_from_image_id(request.image_id)
        except OcrServiceError as exc:
            raise AnalysisServiceError(str(exc)) from exc

        try:
            nutrition_profile = parse_nutrition_text(ocr_result.clean_text)
        except NutritionParserError as exc:
            if str(exc).strip().lower() == "ocr text is empty":
                raise AnalysisServiceError(
                    "I could not read enough text from the image. Please retake a clear photo of the nutrition label."
                ) from exc
            raise AnalysisServiceError(str(exc)) from exc

        vlm_result = AnalysisService._attempt_vlm_answer(request, ocr_result.clean_text)
        if vlm_result is not None:
            vlm_answer, vlm_confidence, source = vlm_result
            qa_answer = vlm_answer
            confidence = vlm_confidence
            answer_source = source
            insights = list(dict.fromkeys(nutrition_profile.to_dict().get("ingredients", [])))
            detected_intent = "vlm"
            health_score = None
            health_label = None
            diet_recommendations: list[str] = []
        else:
            try:
                qa_response = answer_question(nutrition_profile, request.question)
            except QaEngineError as exc:
                raise AnalysisServiceError(str(exc)) from exc
            qa_answer = qa_response.answer
            confidence = qa_response.confidence
            answer_source = qa_response.source
            insights = qa_response.insights
            question_type = qa_response.question_type
            detected_intent = qa_response.detected_intent
            health_score = qa_response.health_score
            health_label = qa_response.health_label
            diet_recommendations = qa_response.diet_recommendations
        if vlm_result is not None:
            question_type = "reasoning"

        localized_answer = translate_text(qa_answer, language)
        localized_insights = translate_list(insights, language)

        return AnalysisResult(
            image_id=request.image_id,
            question=request.question,
            answer=localized_answer,
            confidence=confidence,
            insights=localized_insights,
            question_type=question_type,
            detected_intent=detected_intent,
            source=answer_source,
            health_score=health_score,
            health_label=health_label,
            diet_recommendations=translate_list(diet_recommendations, language),
            language=language,
            ocr_text=ocr_result.clean_text,
            nutrition=nutrition_profile.to_dict(),
        )
