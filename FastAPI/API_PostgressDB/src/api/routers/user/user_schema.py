from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from src.domain.enums.user_enum import UserRole, UserStatus


class UserCreateRequest(BaseModel):
    """Request model for creating a user."""

    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=1, max_length=100, description="Username")
    password: str = Field(..., min_length=8, description="Plain-text password (will be hashed before storage)")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="User status")


class UserUpdateRoleRequest(BaseModel):
    """Request model for updating a user's role."""

    role: UserRole = Field(..., description="The new role to assign to the user")


class UserResponse(BaseModel):
    """Response model for a full user entity (used by GET endpoints)."""

    id: int
    email: str
    username: str
    role: UserRole
    status: UserStatus
    created_at: datetime

    class Config:
        from_attributes = True
