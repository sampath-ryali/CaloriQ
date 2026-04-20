"""Application configuration for the Flask backend."""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
IMAGE_DIR = DATA_DIR / "images"
LOG_DIR = BASE_DIR / "logs"
USERS_FILE = DATA_DIR / "users.json"


class Config:
    """Base configuration loaded from environment variables."""

    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "24"))
    )
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_BYTES", str(16 * 1024 * 1024)))
    UPLOAD_FOLDER = str(IMAGE_DIR)
    JSON_SORT_KEYS = False
    PROPAGATE_EXCEPTIONS = False
    SUPPORTED_LANGUAGES = ("en", "es")
    DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE = str(LOG_DIR / "backend.log")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


def get_config(environment: str | None = None) -> type[Config]:
    """Return the configuration class for the current environment."""

    env_name = (environment or os.getenv("FLASK_ENV") or os.getenv("APP_ENV") or "development").lower()
    config_map: dict[str, type[Config]] = {
        "development": DevelopmentConfig,
        "dev": DevelopmentConfig,
        "testing": TestingConfig,
        "test": TestingConfig,
        "production": ProductionConfig,
        "prod": ProductionConfig,
    }
    return config_map.get(env_name, DevelopmentConfig)
