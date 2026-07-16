from typing import Protocol

from src.domain.enums import user_enum
from src.shared.contract_model import ContractModel


class TokenClaims(ContractModel):
    """The decoded claims carried by a validated authentication token."""

    user_id: int
    role: user_enum.UserRole


class TokenService(Protocol):
    """Port for issuing and validating authentication tokens."""

    def create_access_token(self, user_id: int, role: str) -> str:
        """Create a signed, short-lived access token.

        Args:
            user_id: The unique identifier of the user.
            role: The user role to embed as a claim.

        Returns:
            A signed access token string.
        """
        ...

    def create_refresh_token(self, user_id: int, role: str) -> str:
        """Create a signed, long-lived refresh token.

        Args:
            user_id: The unique identifier of the user.
            role: The user role to embed as a claim.

        Returns:
            A signed refresh token string.
        """
        ...

    def decode_access_token(self, token: str) -> TokenClaims | None:
        """Decode and validate an access token.

        Args:
            token: The access token string to decode.

        Returns:
            The decoded TokenClaims, or None if the token is invalid,
            expired, or not an access token.
        """
        ...

    def decode_refresh_token(self, token: str) -> TokenClaims | None:
        """Decode and validate a refresh token.

        Args:
            token: The refresh token string to decode.

        Returns:
            The decoded TokenClaims, or None if the token is invalid,
            expired, or not a refresh token.
        """
        ...
