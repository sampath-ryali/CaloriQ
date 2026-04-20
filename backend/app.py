"""Flask application entry point for the backend API."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_jwt_extended import JWTManager

from config import Config, DATA_DIR, IMAGE_DIR, LOG_DIR, get_config
from routes import register_blueprints
from services.database import init_database
from utils.errors import register_error_handlers
from utils.logging_utils import configure_logging


jwt = JWTManager()


def create_app(config_object: type[Config] | None = None) -> Flask:
    """Create and configure the Flask application."""

    app = Flask(__name__)
    config_class = config_object or get_config()
    app.config.from_object(config_class)

    _ensure_directories()
    init_database()
    configure_logging(app)
    jwt.init_app(app)
    register_blueprints(app)
    register_error_handlers(app)

    @app.get("/")
    def index() -> tuple[dict[str, str], int]:
        return {"message": "Multimodal Nutrition VQA API is running"}, 200

    @app.get("/health")
    def health() -> tuple[dict[str, str], int]:
        return {"status": "ok"}, 200

    return app


def _ensure_directories() -> None:
    """Create the directories required by the backend."""

    for directory in (DATA_DIR, IMAGE_DIR, LOG_DIR):
        Path(directory).mkdir(parents=True, exist_ok=True)


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", False))
