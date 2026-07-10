"""Data Transfer Objects for authentication operations.

Used directly as API request/response bodies (see ``DTOBase``), so the
field validation rules live on the DTOs themselves.
"""

from pydantic import Field

from src.application.dto_base import DTOBase
from src.domain.enums import user_enum


class LoginDTO(DTOBase):
    """DTO for authenticating a user."""

    username: str = Field(description="Username")
    password: str = Field(description="Plain-text password")


class RefreshTokenDTO(DTOBase):
    """DTO for refreshing an access token."""

    refresh_token: str = Field(description="A valid JWT refresh token")


class TokenDTO(DTOBase):
    """DTO representing the issued token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenClaimsDTO(DTOBase):
    """DTO representing the decoded claims from a JWT token."""

    user_id: int
    role: user_enum.UserRole
