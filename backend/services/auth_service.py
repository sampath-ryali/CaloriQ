"""Authentication business logic for register and login flows."""

from __future__ import annotations

from werkzeug.security import check_password_hash, generate_password_hash

from models.user import User
from services.repositories import UserRepository


class AuthServiceError(Exception):
    """Raised when authentication business rules fail."""


class AuthService:
    """Handles user registration, login, and lookup operations."""

    @staticmethod
    def register_user(username: str, password: str, full_name: str | None = None) -> User:
        normalized_username = username.strip().lower()
        normalized_full_name = (full_name or "").strip() or None
        if not normalized_username:
            raise AuthServiceError("Username is required")
        if not password or len(password) < 8:
            raise AuthServiceError("Password must be at least 8 characters long")

        existing_user = UserRepository.get_by_username(normalized_username)
        if existing_user is not None:
            raise AuthServiceError("Username already exists")

        return UserRepository.create(
            username=normalized_username,
            password_hash=generate_password_hash(password),
            full_name=normalized_full_name,
        )

    @staticmethod
    def authenticate_user(username: str, password: str) -> User:
        normalized_username = username.strip().lower()
        if not normalized_username or not password:
            raise AuthServiceError("Username and password are required")

        user = UserRepository.get_by_username(normalized_username)
        if user is not None and check_password_hash(user.password_hash, password):
            return user

        raise AuthServiceError("Invalid username or password")

    @staticmethod
    def get_user_by_id(user_id: str) -> User | None:
        return UserRepository.get_by_id(user_id)
