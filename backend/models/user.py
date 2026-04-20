"""User domain model used by the authentication layer."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(slots=True)
class User:
    """Serialized user record stored in the local JSON store."""

    id: str
    username: str
    full_name: str | None
    password_hash: str
    created_at: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
