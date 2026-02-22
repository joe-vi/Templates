from datetime import datetime

from pydantic import ConfigDict, EmailStr, Field

from src.api.schemas.base_schema import APIModelBase
from src.domain.enums.user_enum import UserRole, UserStatus


class UserCreateRequest(APIModelBase):
    """Request model for creating a user."""

    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=1, max_length=100, description="Username")
    password: str = Field(..., min_length=8, description="Plain-text password (will be hashed before storage)")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="User status")


class UserUpdateRoleRequest(APIModelBase):
    """Request model for updating a user's role."""

    role: UserRole = Field(..., description="The new role to assign to the user")


class UserResponse(APIModelBase):
    """Response model for a full user entity (used by GET endpoints)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    role: UserRole
    status: UserStatus
    created_at: datetime
