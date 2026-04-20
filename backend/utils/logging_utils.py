"""Logging configuration for the backend API."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask


def configure_logging(app: Flask) -> None:
    """Configure application and file logging."""

    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO"), logging.INFO)
    app.logger.setLevel(log_level)

    if app.logger.handlers:
        return

    log_file = Path(app.config.get("LOG_FILE", "backend.log"))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(log_file, maxBytes=1_048_576, backupCount=3)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)

    app.logger.addHandler(file_handler)
    app.logger.addHandler(stream_handler)
    app.logger.propagate = False
