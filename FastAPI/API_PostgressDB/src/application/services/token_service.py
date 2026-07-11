from typing import Protocol

from src.application.use_cases.auth import auth_dto


class TokenService(Protocol):
    """Port for issuing and validating authentication tokens.

    Implemented by a mechanism-qualified adapter (e.g. PyJWT, python-jose)
    that subclasses this protocol and inherits these docstrings. Use cases and
    the API guard depend on this port only.
    """

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

    def decode_access_token(self, token: str) -> auth_dto.TokenClaimsDTO | None:
        """Decode and validate an access token.

        Args:
            token: The access token string to decode.

        Returns:
            A TokenClaimsDTO with the decoded claims, or None if the token is
            invalid, expired, or not an access token.
        """
        ...

    def decode_refresh_token(self, token: str) -> auth_dto.TokenClaimsDTO | None:
        """Decode and validate a refresh token.

        Args:
            token: The refresh token string to decode.

        Returns:
            A TokenClaimsDTO with the decoded claims, or None if the token is
            invalid, expired, or not a refresh token.
        """
        ...
