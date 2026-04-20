"""Authentication endpoints for register and login flows."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

from services.auth_service import AuthService, AuthServiceError
from utils.auth import require_jwt
from utils.errors import ApiError


auth_bp = Blueprint("auth", __name__)


def _display_name_for_user(user) -> str:
    if user.full_name and user.full_name.strip():
        return user.full_name.strip()
    return user.username.split("@", 1)[0]


def _serialize_user(user) -> dict[str, str]:
    display_name = _display_name_for_user(user)
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "name": display_name,
        "created_at": user.created_at,
    }


@auth_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "")
    password = payload.get("password", "")
    full_name = payload.get("full_name")

    try:
        user = AuthService.register_user(username=username, password=password, full_name=full_name)
    except AuthServiceError as exc:
        raise ApiError(str(exc), status_code=400, error_code="registration_failed") from exc

    token = create_access_token(identity=user.id)
    return (
        jsonify(
            {
                "message": "User registered successfully",
                "user": _serialize_user(user),
                "access_token": token,
            }
        ),
        201,
    )


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "")
    password = payload.get("password", "")

    try:
        user = AuthService.authenticate_user(username=username, password=password)
    except AuthServiceError as exc:
        raise ApiError(str(exc), status_code=401, error_code="authentication_failed") from exc

    token = create_access_token(identity=user.id)
    return (
        jsonify(
            {
                "message": "Login successful",
                "user": _serialize_user(user),
                "access_token": token,
            }
        ),
        200,
    )


@auth_bp.get("/me")
@require_jwt
def me(current_user):
    return jsonify({"user": current_user.to_dict()}), 200
