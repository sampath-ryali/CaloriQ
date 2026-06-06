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


@health_bp.get("/check-hf")
def check_hf():
    import os
    import requests
    
    token = os.getenv("HF_TOKEN", "")
    token_present = len(token) > 0
    token_masked = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "too_short"
    
    hf_url = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct"
    headers = {
        "Content-Type": "application/json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    result = {}
    try:
        res = requests.post(
            hf_url,
            json={"inputs": "Reply with exactly: HF_OK", "parameters": {"temperature": 0.7, "max_new_tokens": 10}},
            headers=headers,
            timeout=15
        )
        result["status_code"] = res.status_code
        result["text"] = res.text
    except Exception as exc:
        result["error"] = str(exc)
        
    return {
        "token_present": token_present,
        "token_masked": token_masked if token_present else "none",
        "huggingface": result
    }, 200
