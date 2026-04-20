"""Database engine and session management for persistent storage."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

from config import BASE_DIR


DEFAULT_DB_PATH = BASE_DIR / "data" / "caloriq.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

_ENGINE_KWARGS: dict[str, object] = {
    "future": True,
    "pool_pre_ping": True,
}
if DATABASE_URL.startswith("sqlite"):
    _ENGINE_KWARGS["connect_args"] = {"check_same_thread": False}

engine: Engine = create_engine(DATABASE_URL, **_ENGINE_KWARGS)
SessionLocal = scoped_session(
    sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
)
Base = declarative_base()


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record):
    """Enable SQLite foreign keys for relational integrity."""

    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@contextmanager
def db_session() -> Generator:
    """Yield a transaction-scoped SQLAlchemy session."""

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database() -> None:
    """Create database schema and migrate legacy JSON users if present."""

    from services import db_models  # Imported lazily so metadata is populated.
    from services.legacy_migration import migrate_users_json_to_db

    Base.metadata.create_all(bind=engine)
    _migrate_users_table()
    migrate_users_json_to_db()


def _migrate_users_table() -> None:
    """Apply lightweight schema updates for existing SQLite databases."""

    if not DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as connection:
        pragma_rows = connection.execute(text("PRAGMA table_info(users)")).fetchall()
        existing_columns = {str(row[1]) for row in pragma_rows}

        if "full_name" not in existing_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(255)"))
