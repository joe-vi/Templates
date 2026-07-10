"""Data Transfer Objects for user operations.

Used directly as API request/response bodies (see ``DTOBase``), so the
field validation rules live on the DTOs themselves.
"""

from datetime import datetime

from pydantic import EmailStr, Field

from src.application.dto_base import DTOBase
from src.domain.enums import user_enum


class UpdateUserRoleDTO(DTOBase):
    """DTO for updating a user's role."""

    user_id: int
    role: user_enum.UserRole = Field(
        description="The new role to assign to the user"
    )


class CreateUserDTO(DTOBase):
    """DTO for creating a user."""

    email: EmailStr = Field(description="User email address")
    username: str = Field(min_length=1, max_length=100, description="Username")
    password: str = Field(
        min_length=8,
        description="Plain-text password (will be hashed before storage)",
    )
    role: user_enum.UserRole = user_enum.UserRole.USER
    status: user_enum.UserStatus = user_enum.UserStatus.ACTIVE


class UserDTO(DTOBase):
    """DTO representing a user."""

    id: int
    email: str
    username: str
    role: user_enum.UserRole
    status: user_enum.UserStatus
    created_at: datetime
