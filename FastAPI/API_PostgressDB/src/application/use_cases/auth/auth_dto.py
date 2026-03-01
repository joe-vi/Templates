"""Data Transfer Objects for authentication operations."""

from dataclasses import dataclass

from src.domain.enums import user_enum


@dataclass(frozen=True)
class LoginDTO:
    """DTO for authenticating a user."""

    username: str
    password: str


@dataclass(frozen=True)
class TokenDTO:
    """DTO representing the issued token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass(frozen=True)
class TokenClaimsDTO:
    """DTO representing the decoded claims from a JWT token."""

    user_id: int
    role: user_enum.UserRole
