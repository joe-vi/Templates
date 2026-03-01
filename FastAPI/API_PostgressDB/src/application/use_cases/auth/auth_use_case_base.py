"""Abstract base class for the authentication use case."""

from abc import ABC, abstractmethod

from src.application.use_cases.auth import auth_dto
from src.domain.enums import operation_results


class AuthUseCaseBase(ABC):
    """Abstract base class for authentication use case."""

    @abstractmethod
    async def login(
        self, login_dto: auth_dto.LoginDTO
    ) -> tuple[operation_results.LoginResult, auth_dto.TokenDTO | None]:
        """Authenticate a user and return a JWT token pair.

        Args:
            login_dto: The DTO containing the username and password.

        Returns:
            A tuple of (result, token_dto). token_dto is None on any failure.
        """

    @abstractmethod
    async def refresh_token(
        self, refresh_token: str
    ) -> tuple[operation_results.LoginResult, auth_dto.TokenDTO | None]:
        """Issue a new token pair using a valid refresh token.

        Args:
            refresh_token: The JWT refresh token string.

        Returns:
            A tuple of (result, token_dto). token_dto is None on any failure.
        """
