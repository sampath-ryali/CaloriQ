"""Blueprint registration for the backend API."""

from __future__ import annotations

from flask import Flask

from routes.auth import auth_bp
from routes.chat import chat_bp
from routes.health import health_bp
from routes.qa import qa_bp
from routes.upload import upload_bp


def register_blueprints(app: Flask) -> None:
    """Register API blueprints on the Flask application."""

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(upload_bp, url_prefix="/api")
    app.register_blueprint(qa_bp, url_prefix="/api")

