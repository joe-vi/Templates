from pydantic import Field

from src.api.schemas.base_schema import CamelCaseModel


class LoginRequest(CamelCaseModel):
    """Request model for user authentication."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Plain-text password")


class RefreshTokenRequest(CamelCaseModel):
    """Request model for refreshing an access token."""

    refresh_token: str = Field(..., description="A valid JWT refresh token")


class TokenResponse(CamelCaseModel):
    """Response model returned on successful authentication or token refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
