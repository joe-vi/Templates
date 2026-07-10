"""Authentication use case."""

from injector import inject

from src.application.services.logger import Logger
from src.application.services.password_hasher import PasswordHasher
from src.application.services.token_service import TokenService
from src.application.use_cases.auth import auth_dto
from src.domain.enums import operation_results, user_enum
from src.domain.repositories.user.user_repository import UserRepository


class AuthUseCase:
    """Application logic for authentication operations."""

    @inject
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        logger: Logger,
    ) -> None:
        """Initialize the authentication use case.

        Args:
            user_repository: The user repository port for credential lookup.
            password_hasher: The port for verifying hashed passwords.
            token_service: The port for creating and decoding JWT tokens.
            logger: The structured logger port for recording login events.
        """
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._logger = logger

    async def login(
        self, login_dto: auth_dto.LoginDTO
    ) -> tuple[operation_results.LoginResult, auth_dto.TokenDTO | None]:
        """Authenticate a user and issue a token pair on success."""
        self._logger.info("Login attempt", username=login_dto.username)

        user = await self._user_repository.get_by_username(login_dto.username)

        if user is None or user.hashed_password is None or user.id is None:
            self._logger.warning(
                "Login failed: user not found", username=login_dto.username
            )
            return (operation_results.LoginResult.INVALID_CREDENTIALS, None)

        if not self._password_hasher.verify(
            login_dto.password, user.hashed_password
        ):
            self._logger.warning(
                "Login failed: invalid password", username=login_dto.username
            )
            return (operation_results.LoginResult.INVALID_CREDENTIALS, None)

        if user.status == user_enum.UserStatus.INACTIVE:
            self._logger.warning(
                "Login failed: account inactive", username=login_dto.username
            )
            return (operation_results.LoginResult.USER_INACTIVE, None)

        access_token = self._token_service.create_access_token(
            user.id, user.role
        )
        refresh_token = self._token_service.create_refresh_token(
            user.id, user.role
        )
        self._logger.info("Login successful", username=login_dto.username)
        return (
            operation_results.LoginResult.SUCCESS,
            auth_dto.TokenDTO(
                access_token=access_token, refresh_token=refresh_token
            ),
        )

    async def refresh_token(
        self, refresh_token: str
    ) -> tuple[operation_results.LoginResult, auth_dto.TokenDTO | None]:
        """Issue a new token pair from a valid refresh token."""
        token_claims = self._token_service.decode_refresh_token(refresh_token)

        if token_claims is None:
            return (operation_results.LoginResult.INVALID_CREDENTIALS, None)

        access_token = self._token_service.create_access_token(
            token_claims.user_id, token_claims.role
        )
        new_refresh_token = self._token_service.create_refresh_token(
            token_claims.user_id, token_claims.role
        )
        return (
            operation_results.LoginResult.SUCCESS,
            auth_dto.TokenDTO(
                access_token=access_token, refresh_token=new_refresh_token
            ),
        )
