"""One-time migration helpers for moving legacy JSON users into SQL tables."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select

from config import USERS_FILE
from services.database import db_session
from services.db_models import UserEntity


def migrate_users_json_to_db() -> None:
    """Import legacy users.json data if users table is currently empty."""

    if not USERS_FILE.exists():
        return

    raw = USERS_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        return

    try:
        legacy_users = json.loads(raw)
    except json.JSONDecodeError:
        return

    if not isinstance(legacy_users, list) or not legacy_users:
        return

    with db_session() as session:
        existing_count = session.query(UserEntity).count()
        if existing_count > 0:
            return

        for user in legacy_users:
            user_id = str(user.get("id", "")).strip()
            username = str(user.get("username", "")).strip().lower()
            password_hash = str(user.get("password_hash", "")).strip()
            created_at_raw = str(user.get("created_at", "")).strip()
            if not user_id or not username or not password_hash:
                continue

            try:
                created_at = datetime.fromisoformat(created_at_raw) if created_at_raw else datetime.now(timezone.utc)
            except ValueError:
                created_at = datetime.now(timezone.utc)

            if session.scalar(select(UserEntity).where(UserEntity.id == user_id)) is not None:
                continue

            if session.scalar(select(UserEntity).where(UserEntity.username == username)) is not None:
                continue

            session.add(
                UserEntity(
                    id=user_id,
                    username=username,
                    full_name=(str(user.get("full_name", "")).strip() or None),
                    password_hash=password_hash,
                    created_at=created_at,
                )
            )
