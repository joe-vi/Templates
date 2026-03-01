"""Pydantic request and response schemas for auth endpoints."""

from pydantic import Field

from src.api.schemas import base_schema


class LoginRequest(base_schema.APIModelBase):
    """Request model for user authentication."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Plain-text password")


class RefreshTokenRequest(base_schema.APIModelBase):
    """Request model for refreshing an access token."""

    refresh_token: str = Field(..., description="A valid JWT refresh token")


class TokenResponse(base_schema.APIModelBase):
    """Response model returned on successful authentication or token refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
