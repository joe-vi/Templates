from injector import inject

from src.application.use_cases.auth import auth_contracts
from src.domain.enums import operation_results
from src.domain.repositories.user.user_repository import UserRepository
from src.ports.logger import Logger
from src.ports.password_hasher import PasswordHasher
from src.ports.token_service import TokenService


class LoginUseCase:
    """Authenticates a user and issues a token pair."""

    @inject
    def __init__(
        self, user_repository: UserRepository, password_hasher: PasswordHasher, token_service: TokenService, logger: Logger
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._logger = logger

    async def execute(
        self, login_request: auth_contracts.LoginRequest
    ) -> tuple[operation_results.LoginResult, auth_contracts.TokenResponse | None]:
        """Authenticate a user and issue a token pair on success.

        Args:
            login_request: The submitted username and plain-text password.

        Returns:
            A tuple of (result, tokens): the TokenResponse on success, None on
            any failure result (unknown user, wrong password, inactive account).
        """
        self._logger.info("Login attempt", username=login_request.username)

        user = await self._user_repository.get_by_username(login_request.username)

        if user is None or user.hashed_password is None or user.id is None:
            self._logger.warning("Login failed: user not found", username=login_request.username)
            return (operation_results.LoginResult.INVALID_CREDENTIALS, None)

        if not self._password_hasher.verify(login_request.password, user.hashed_password):
            self._logger.warning("Login failed: invalid password", username=login_request.username)
            return (operation_results.LoginResult.INVALID_CREDENTIALS, None)

        if not user.is_active:
            self._logger.warning("Login failed: account inactive", username=login_request.username)
            return (operation_results.LoginResult.USER_INACTIVE, None)

        access_token = self._token_service.create_access_token(user.id, user.role)
        refresh_token = self._token_service.create_refresh_token(user.id, user.role)
        self._logger.info("Login successful", username=login_request.username)
        return (operation_results.LoginResult.SUCCESS, auth_contracts.TokenResponse(access_token=access_token, refresh_token=refresh_token))
