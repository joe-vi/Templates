from dataclasses import dataclass, field
from datetime import datetime

from src.domain.enums.user_enum import UserRole, UserStatus


@dataclass
class User:
    """Domain entity representing a user."""

    id: int | None
    email: str
    username: str
    hashed_password: str | None = None
    role: UserRole = field(default=UserRole.USER)
    status: UserStatus = field(default=UserStatus.ACTIVE)
    created_at: datetime | None = None
