"""Repository layer for database-backed auth and chat persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from models.user import User
from services.database import db_session
from services.db_models import ChatMessageEntity, ChatSessionEntity, MessageRole, UserEntity


class UserRepository:
    @staticmethod
    def get_by_username(username: str) -> User | None:
        with db_session() as session:
            entity = session.scalar(select(UserEntity).where(UserEntity.username == username))
            if entity is None:
                return None
            return User(
                id=entity.id,
                username=entity.username,
                full_name=entity.full_name,
                password_hash=entity.password_hash,
                created_at=entity.created_at.isoformat(),
            )

    @staticmethod
    def get_by_id(user_id: str) -> User | None:
        with db_session() as session:
            entity = session.scalar(select(UserEntity).where(UserEntity.id == user_id))
            if entity is None:
                return None
            return User(
                id=entity.id,
                username=entity.username,
                full_name=entity.full_name,
                password_hash=entity.password_hash,
                created_at=entity.created_at.isoformat(),
            )

    @staticmethod
    def create(username: str, password_hash: str, full_name: str | None = None) -> User:
        now = datetime.now(timezone.utc)
        entity = UserEntity(
            id=str(uuid4()),
            username=username,
            full_name=full_name,
            password_hash=password_hash,
            created_at=now,
        )
        with db_session() as session:
            session.add(entity)
        return User(
            id=entity.id,
            username=entity.username,
            full_name=entity.full_name,
            password_hash=entity.password_hash,
            created_at=entity.created_at.isoformat(),
        )


class ChatRepository:
    @staticmethod
    def _ensure_chat(session, user_id: str, chat_id: str) -> ChatSessionEntity:
        chat = session.scalar(
            select(ChatSessionEntity).where(
                ChatSessionEntity.id == chat_id,
                ChatSessionEntity.user_id == user_id,
            )
        )
        if chat is None:
            chat = ChatSessionEntity(id=chat_id, user_id=user_id, title="New Analysis")
            session.add(chat)
            session.flush()
        return chat

    @staticmethod
    def save_exchange(
        *,
        user_id: str,
        chat_id: str,
        user_text: str,
        assistant_text: str,
        image_id: str | None,
    ) -> None:
        now = datetime.now(timezone.utc)
        with db_session() as session:
            chat = ChatRepository._ensure_chat(session, user_id, chat_id)
            chat.updated_at = now

            session.add(
                ChatMessageEntity(
                    id=str(uuid4()),
                    chat_id=chat.id,
                    user_id=user_id,
                    role=MessageRole.user.value,
                    content=user_text,
                    image_id=image_id,
                    created_at=now,
                )
            )
            session.add(
                ChatMessageEntity(
                    id=str(uuid4()),
                    chat_id=chat.id,
                    user_id=user_id,
                    role=MessageRole.assistant.value,
                    content=assistant_text,
                    image_id=None,
                    created_at=now,
                )
            )

    @staticmethod
    def list_chats(user_id: str, limit: int = 50) -> list[dict[str, str]]:
        with db_session() as session:
            rows = session.scalars(
                select(ChatSessionEntity)
                .where(ChatSessionEntity.user_id == user_id)
                .order_by(ChatSessionEntity.updated_at.desc())
                .limit(limit)
            ).all()
            return [
                {
                    "id": row.id,
                    "title": row.title or "New Analysis",
                    "created_at": row.created_at.isoformat(),
                    "updated_at": row.updated_at.isoformat(),
                }
                for row in rows
            ]

    @staticmethod
    def list_messages(user_id: str, chat_id: str, limit: int = 500) -> list[dict[str, str | None]]:
        with db_session() as session:
            rows = session.scalars(
                select(ChatMessageEntity)
                .where(
                    ChatMessageEntity.user_id == user_id,
                    ChatMessageEntity.chat_id == chat_id,
                )
                .order_by(ChatMessageEntity.created_at.asc())
                .limit(limit)
            ).all()
            return [
                {
                    "id": row.id,
                    "chat_id": row.chat_id,
                    "role": row.role,
                    "content": row.content,
                    "image_id": row.image_id,
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ]

    @staticmethod
    def chat_exists_for_user(user_id: str, chat_id: str) -> bool:
        with db_session() as session:
            row = session.scalar(
                select(ChatSessionEntity.id).where(
                    ChatSessionEntity.id == chat_id,
                    ChatSessionEntity.user_id == user_id,
                )
            )
            return row is not None
