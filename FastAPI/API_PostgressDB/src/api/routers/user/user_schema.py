"""Pydantic request and response schemas for user endpoints."""

from datetime import datetime

from pydantic import ConfigDict, EmailStr, Field

from src.api.schemas import base_schema
from src.domain.enums import user_enum


class UserCreateRequest(base_schema.APIModelBase):
    """Request model for creating a user."""

    email: EmailStr = Field(..., description="User email address")
    username: str = Field(
        ..., min_length=1, max_length=100, description="Username"
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Plain-text password (will be hashed before storage)",
    )
    role: user_enum.UserRole = Field(
        default=user_enum.UserRole.USER, description="User role"
    )
    status: user_enum.UserStatus = Field(
        default=user_enum.UserStatus.ACTIVE, description="User status"
    )


class UserUpdateRoleRequest(base_schema.APIModelBase):
    """Request model for updating a user's role."""

    role: user_enum.UserRole = Field(
        ..., description="The new role to assign to the user"
    )


class UserResponse(base_schema.APIModelBase):
    """Response model for a full user entity (used by GET endpoints)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    role: user_enum.UserRole
    status: user_enum.UserStatus
    created_at: datetime
