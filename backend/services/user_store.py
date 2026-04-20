"""Local JSON-backed storage for users."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from config import BASE_DIR


USERS_FILE = BASE_DIR / "data" / "users.json"
_LOCK = Lock()


def ensure_store() -> None:
    """Ensure the backing user store exists."""

    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        USERS_FILE.write_text("[]", encoding="utf-8")


def load_users() -> list[dict[str, str]]:
    """Load all users from the JSON store."""

    ensure_store()
    with _LOCK:
        raw_data = USERS_FILE.read_text(encoding="utf-8")
        if not raw_data.strip():
            return []
        return json.loads(raw_data)


def save_users(users: list[dict[str, str]]) -> None:
    """Persist all users to the JSON store."""

    ensure_store()
    with _LOCK:
        USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")
