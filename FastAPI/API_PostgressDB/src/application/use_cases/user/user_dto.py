from dataclasses import dataclass
from datetime import datetime

from src.domain.enums.user_enum import UserRole, UserStatus


@dataclass(frozen=True)
class UpdateUserRoleDTO:
    """DTO for updating a user's role."""

    user_id: int
    role: UserRole


@dataclass(frozen=True)
class CreateUserDTO:
    """DTO for creating a user."""

    email: str
    username: str
    password: str
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE


@dataclass(frozen=True)
class UserDTO:
    """DTO representing a user."""

    id: int
    email: str
    username: str
    role: UserRole
    status: UserStatus
    created_at: datetime
