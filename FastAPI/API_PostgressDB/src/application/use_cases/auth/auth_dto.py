from pydantic import Field

from src.application.dto_base import DTOBase
from src.domain.enums import user_enum


class LoginDTO(DTOBase):
    """DTO for authenticating a user; doubles as the request body."""

    username: str = Field(description="Username")
    password: str = Field(description="Plain-text password")


class RefreshTokenDTO(DTOBase):
    """DTO for refreshing an access token; doubles as the request body."""

    refresh_token: str = Field(description="A valid JWT refresh token")


class TokenDTO(DTOBase):
    """DTO representing the issued token pair; doubles as the response body."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenClaimsDTO(DTOBase):
    """DTO representing the decoded claims from a validated token."""

    user_id: int
    role: user_enum.UserRole
