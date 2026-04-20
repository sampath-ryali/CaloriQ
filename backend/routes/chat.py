"""Chat history endpoints backed by persistent database storage."""

from __future__ import annotations

from flask import Blueprint, jsonify

from services.repositories import ChatRepository
from utils.auth import require_jwt
from utils.errors import ApiError


chat_bp = Blueprint("chat", __name__)


@chat_bp.get("/chats")
@require_jwt
def list_chats(current_user):
    chats = ChatRepository.list_chats(user_id=current_user.id)
    return jsonify({"chats": chats}), 200


@chat_bp.get("/chats/<chat_id>/messages")
@require_jwt
def list_chat_messages(chat_id: str, current_user):
    if not ChatRepository.chat_exists_for_user(user_id=current_user.id, chat_id=chat_id):
        raise ApiError("Chat not found", status_code=404, error_code="chat_not_found")

    messages = ChatRepository.list_messages(user_id=current_user.id, chat_id=chat_id)
    return jsonify({"chat_id": chat_id, "messages": messages}), 200
