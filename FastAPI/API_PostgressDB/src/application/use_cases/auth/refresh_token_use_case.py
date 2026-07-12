from injector import inject

from src.application.services.token_service import TokenService
from src.application.use_cases.auth import auth_dto
from src.domain.enums import operation_results


class RefreshTokenUseCase:
    """Issues a new token pair from a refresh token."""

    @inject
    def __init__(self, token_service: TokenService) -> None:
        self._token_service = token_service

    async def execute(self, refresh_token: str) -> tuple[operation_results.LoginResult, auth_dto.TokenDTO | None]:
        """Issue a new token pair from a valid refresh token.

        Args:
            refresh_token: The refresh token presented by the caller.

        Returns:
            A tuple of (result, tokens): the new TokenDTO on success, None
            when the refresh token is invalid or expired.
        """
        token_claims = self._token_service.decode_refresh_token(refresh_token)

        if token_claims is None:
            return (operation_results.LoginResult.INVALID_CREDENTIALS, None)

        access_token = self._token_service.create_access_token(token_claims.user_id, token_claims.role)
        new_refresh_token = self._token_service.create_refresh_token(token_claims.user_id, token_claims.role)
        return (operation_results.LoginResult.SUCCESS, auth_dto.TokenDTO(access_token=access_token, refresh_token=new_refresh_token))
