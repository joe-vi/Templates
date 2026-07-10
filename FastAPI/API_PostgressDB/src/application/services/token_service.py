"""JWT token service port (structural interface)."""

from typing import Protocol

from src.application.use_cases.auth import auth_dto


class TokenService(Protocol):
    """Port for JWT token operations.

    Implement with a provider-specific adapter (e.g. PyJWT, python-jose) and
    wire it in the dependency providers. Use cases depend only on this
    protocol, so switching providers requires no changes outside the
    infrastructure layer.
    """

    def create_access_token(self, user_id: int, role: str) -> str:
        """Create a signed JWT access token.

        Args:
            user_id: The unique identifier of the user.
            role: The user role to embed in the token.

        Returns:
            A signed JWT access token string.
        """
        ...

    def create_refresh_token(self, user_id: int, role: str) -> str:
        """Create a signed JWT refresh token.

        Args:
            user_id: The unique identifier of the user.
            role: The user role to embed in the token.

        Returns:
            A signed JWT refresh token string.
        """
        ...

    def decode_access_token(self, token: str) -> auth_dto.TokenClaimsDTO | None:
        """Decode and validate a JWT access token.

        Args:
            token: The JWT access token string to decode.

        Returns:
            A TokenClaimsDTO with the decoded claims, or None if the token
            is invalid or expired.
        """
        ...

    def decode_refresh_token(
        self, token: str
    ) -> auth_dto.TokenClaimsDTO | None:
        """Decode and validate a JWT refresh token.

        Args:
            token: The JWT refresh token string to decode.

        Returns:
            A TokenClaimsDTO with the decoded claims, or None if the token
            is invalid or expired.
        """
        ...
