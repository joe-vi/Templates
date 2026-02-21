from abc import ABC, abstractmethod

from src.application.use_cases.auth.auth_dto import LoginDTO, TokenDTO
from src.domain.enums.operation_results import LoginResult


class AuthUseCaseBase(ABC):
    """Abstract base class for authentication use case."""

    @abstractmethod
    async def login(self, login_dto: LoginDTO) -> tuple[LoginResult, TokenDTO | None]:
        """Authenticate a user and return a JWT token pair.

        Args:
            login_dto: The DTO containing the username and password.

        Returns:
            A tuple of (result, token_dto). token_dto is None on any failure.
        """

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> tuple[LoginResult, TokenDTO | None]:
        """Issue a new token pair using a valid refresh token.

        Args:
            refresh_token: The JWT refresh token string.

        Returns:
            A tuple of (result, token_dto). token_dto is None on any failure.
        """
