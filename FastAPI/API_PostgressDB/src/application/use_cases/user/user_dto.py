"""Data Transfer Objects for user operations."""

from dataclasses import dataclass
from datetime import datetime

from src.domain.enums import user_enum


@dataclass(frozen=True)
class UpdateUserRoleDTO:
    """DTO for updating a user's role."""

    user_id: int
    role: user_enum.UserRole


@dataclass(frozen=True)
class CreateUserDTO:
    """DTO for creating a user."""

    email: str
    username: str
    password: str
    role: user_enum.UserRole = user_enum.UserRole.USER
    status: user_enum.UserStatus = user_enum.UserStatus.ACTIVE


@dataclass(frozen=True)
class UserDTO:
    """DTO representing a user."""

    id: int
    email: str
    username: str
    role: user_enum.UserRole
    status: user_enum.UserStatus
    created_at: datetime
