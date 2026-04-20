"""Shared API error handling utilities."""

from __future__ import annotations

from dataclasses import dataclass

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


@dataclass(slots=True)
class ApiError(Exception):
    """Serializable API error with status code and optional details."""

    message: str
    status_code: int = 400
    error_code: str = "api_error"
    details: dict[str, object] | None = None


def register_error_handlers(app: Flask) -> None:
    """Register JSON error handlers for the application."""

    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        payload = {
            "error": {
                "message": error.message,
                "code": error.error_code,
                "details": error.details or {},
            }
        }
        return jsonify(payload), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        payload = {
            "error": {
                "message": error.description,
                "code": error.name.lower().replace(" ", "_"),
                "details": {},
            }
        }
        return jsonify(payload), error.code or 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        app.logger.exception("Unhandled exception", exc_info=error)
        payload = {
            "error": {
                "message": "An unexpected error occurred",
                "code": "internal_server_error",
                "details": {},
            }
        }
        return jsonify(payload), 500
