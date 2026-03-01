"""Abstract base class for the JWT token service."""

from abc import ABC, abstractmethod

from src.application.use_cases.auth import auth_dto


class TokenServiceBase(ABC):
    """Abstract base class for JWT token operations.

    Implement this interface with a provider-specific class (e.g. PyJWT,
    python-jose) and bind it in the DI container. Use cases depend only on
    this interface, so switching providers requires no changes outside the
    infrastructure layer.
    """

    @abstractmethod
    def create_access_token(self, user_id: int, role: str) -> str:
        """Create a signed JWT access token.

        Args:
            user_id: The unique identifier of the user.
            role: The user role to embed in the token.

        Returns:
            A signed JWT access token string.
        """

    @abstractmethod
    def create_refresh_token(self, user_id: int, role: str) -> str:
        """Create a signed JWT refresh token.

        Args:
            user_id: The unique identifier of the user.
            role: The user role to embed in the token.

        Returns:
            A signed JWT refresh token string.
        """

    @abstractmethod
    def decode_access_token(self, token: str) -> auth_dto.TokenClaimsDTO | None:
        """Decode and validate a JWT access token.

        Args:
            token: The JWT access token string to decode.

        Returns:
            A TokenClaimsDTO with the decoded claims, or None if the token
            is invalid or expired.
        """

    @abstractmethod
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
