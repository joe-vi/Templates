from datetime import datetime

from pydantic import EmailStr, Field

from src.domain.enums import user_enum
from src.shared.contract_model import ContractModel


class CreateUserRequest(ContractModel):
    """Request body for creating a user."""

    email: EmailStr = Field(description="User email address")
    username: str = Field(min_length=1, max_length=100, description="Username")
    password: str = Field(min_length=8, description="Plain-text password (will be hashed before storage)")
    role: user_enum.UserRole = user_enum.UserRole.USER
    status: user_enum.UserStatus = user_enum.UserStatus.ACTIVE


class UserResponse(ContractModel):
    """Response body representing a persisted user."""

    id: int
    email: str
    username: str
    role: user_enum.UserRole
    status: user_enum.UserStatus
    created_at: datetime
