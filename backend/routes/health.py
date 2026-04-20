"""Health and readiness endpoints."""

from __future__ import annotations

from flask import Blueprint


health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def api_health() -> tuple[dict[str, str], int]:
    return {"status": "ok", "service": "backend"}, 200


@health_bp.get("/ready")
def ready() -> tuple[dict[str, str], int]:
    return {"status": "ready"}, 200
