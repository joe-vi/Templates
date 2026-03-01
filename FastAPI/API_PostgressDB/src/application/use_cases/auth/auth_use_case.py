"""Authentication use case implementation."""

from injector import inject

from src.application.services import (
    custom_logger_base,
    password_hasher_base,
    token_service_base,
)
from src.application.use_cases.auth import auth_dto, auth_use_case_base
from src.domain.enums import operation_results, user_enum
from src.domain.repositories.user import user_repository_base


class AuthUseCase(auth_use_case_base.AuthUseCaseBase):
    """Use case for authentication operations."""

    @inject
    def __init__(
        self,
        user_repository: user_repository_base.UserRepositoryBase,
        password_hasher: password_hasher_base.PasswordHasherBase,
        token_service: token_service_base.TokenServiceBase,
        logger: custom_logger_base.CustomLoggerBase,
    ) -> None:
        """Initialize the authentication use case.

        Args:
            user_repository: The user repository for credential lookup.
            password_hasher: The service for verifying hashed passwords.
            token_service: The service for creating and decoding JWT tokens.
            logger: The structured logger for recording login events.
        """
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._logger = logger

    async def login(
        self, login_dto: auth_dto.LoginDTO
    ) -> tuple[operation_results.LoginResult, auth_dto.TokenDTO | None]:
        self._logger.info("Login attempt", username=login_dto.username)

        user = await self._user_repository.get_by_username(login_dto.username)

        if user is None or user.hashed_password is None:
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
        )  # type: ignore[arg-type]
        refresh_token = self._token_service.create_refresh_token(
            user.id, user.role
        )  # type: ignore[arg-type]
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
