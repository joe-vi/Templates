from injector import inject

from src.application.services.logger import Logger
from src.application.services.password_hasher import PasswordHasher
from src.application.services.token_service import TokenService
from src.application.use_cases.auth import auth_dto
from src.domain.enums import operation_results
from src.domain.repositories.user.user_repository import UserRepository


class LoginUseCase:
    """Application logic for authenticating a user.

    One use case class per operation: routes and tests depend on this class
    directly (mock with ``AsyncMock(spec=LoginUseCase)``). Depends only on
    ports; the concrete adapters are supplied by the composition root.
    """

    @inject
    def __init__(
        self, user_repository: UserRepository, password_hasher: PasswordHasher, token_service: TokenService, logger: Logger
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._logger = logger

    async def execute(self, login_dto: auth_dto.LoginDTO) -> tuple[operation_results.LoginResult, auth_dto.TokenDTO | None]:
        """Authenticate a user and issue a token pair on success.

        Args:
            login_dto: The submitted username and plain-text password.

        Returns:
            A tuple of (result, tokens): the TokenDTO on success, None on any
            failure result (unknown user, wrong password, inactive account).
        """
        self._logger.info("Login attempt", username=login_dto.username)

        user = await self._user_repository.get_by_username(login_dto.username)

        if user is None or user.hashed_password is None or user.id is None:
            self._logger.warning("Login failed: user not found", username=login_dto.username)
            return (operation_results.LoginResult.INVALID_CREDENTIALS, None)

        if not self._password_hasher.verify(login_dto.password, user.hashed_password):
            self._logger.warning("Login failed: invalid password", username=login_dto.username)
            return (operation_results.LoginResult.INVALID_CREDENTIALS, None)

        if not user.is_active:
            self._logger.warning("Login failed: account inactive", username=login_dto.username)
            return (operation_results.LoginResult.USER_INACTIVE, None)

        access_token = self._token_service.create_access_token(user.id, user.role)
        refresh_token = self._token_service.create_refresh_token(user.id, user.role)
        self._logger.info("Login successful", username=login_dto.username)
        return (operation_results.LoginResult.SUCCESS, auth_dto.TokenDTO(access_token=access_token, refresh_token=refresh_token))
