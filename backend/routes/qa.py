"""Question answering endpoint for nutrition label images."""

from __future__ import annotations

from uuid import uuid4

from flask import Blueprint, jsonify, request

from models.ask_question_request import AskQuestionRequest
from services.analysis_service import AnalysisService, AnalysisServiceError
from services.repositories import ChatRepository
from utils.auth import require_jwt
from utils.errors import ApiError


qa_bp = Blueprint("qa", __name__)


@qa_bp.post("/ask-question")
@require_jwt
def ask_question(current_user):
    payload = request.get_json(silent=True) or {}
    image_id = str(payload.get("image_id", "")).strip()
    question = str(payload.get("question", "")).strip()
    chat_id = str(payload.get("chat_id", "")).strip() or str(uuid4())
    language = str(payload.get("language", "en")).strip() or "en"

    if not image_id:
        raise ApiError("image_id is required", status_code=400, error_code="missing_image_id")
    if not question:
        raise ApiError("question is required", status_code=400, error_code="missing_question")

    request_model = AskQuestionRequest(image_id=image_id, question=question, language=language)

    try:
        result = AnalysisService.analyze(request_model)
    except AnalysisServiceError as exc:
        ChatRepository.save_exchange(
            user_id=current_user.id,
            chat_id=chat_id,
            user_text=question,
            assistant_text="I could not analyze this image right now. Please try a clearer nutrition-label image.",
            image_id=image_id,
        )
        raise ApiError(str(exc), status_code=422, error_code="analysis_failed") from exc

    response_payload = result.to_dict()
    response_payload["user_id"] = current_user.id
    response_payload["chat_id"] = chat_id

    ChatRepository.save_exchange(
        user_id=current_user.id,
        chat_id=chat_id,
        user_text=question,
        assistant_text=result.answer,
        image_id=image_id,
    )

    return jsonify(response_payload), 200
