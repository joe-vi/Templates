from pydantic import Field

from src.shared.contract_model import ContractModel


class LoginRequest(ContractModel):
    """Request body for authenticating a user."""

    username: str = Field(description="Username")
    password: str = Field(description="Plain-text password")


class RefreshTokenRequest(ContractModel):
    """Request body for refreshing an access token."""

    refresh_token: str = Field(description="A valid JWT refresh token")


class TokenResponse(ContractModel):
    """Response body carrying the issued token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
