"""SQLAlchemy ORM entities for users, chats, and messages."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.database import Base


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


class UserEntity(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    chats: Mapped[list["ChatSessionEntity"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class ChatSessionEntity(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user: Mapped["UserEntity"] = relationship(back_populates="chats")
    messages: Mapped[list["ChatMessageEntity"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )


class ChatMessageEntity(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    chat_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    chat: Mapped["ChatSessionEntity"] = relationship(back_populates="messages")


Index("ix_chat_messages_chat_created", ChatMessageEntity.chat_id, ChatMessageEntity.created_at)
Index("ix_chat_sessions_user_updated", ChatSessionEntity.user_id, ChatSessionEntity.updated_at)
