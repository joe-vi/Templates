"""User domain entity."""

from dataclasses import dataclass, field
from datetime import datetime

from src.domain.enums import user_enum


@dataclass
class User:
    """Domain entity representing a user."""

    id: int | None
    email: str
    username: str
    hashed_password: str | None = None
    role: user_enum.UserRole = field(default=user_enum.UserRole.USER)
    status: user_enum.UserStatus = field(default=user_enum.UserStatus.ACTIVE)
    created_at: datetime | None = None
