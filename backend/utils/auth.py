"""Authentication helpers for protecting routes with JWT."""

from __future__ import annotations

from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from services.auth_service import AuthService


def require_jwt(fn):
    """Protect a route with JWT and verify the user still exists."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        if user is None:
            return jsonify({"error": {"message": "User not found", "code": "user_not_found", "details": {}}}), 404
        return fn(*args, current_user=user, **kwargs)

    return wrapper
