from fastapi import APIRouter, HTTPException, status

from src.api.dependencies.injected import Injected
from src.application.use_cases.auth import auth_contracts
from src.application.use_cases.auth.refresh_token_use_case import RefreshTokenUseCase
from src.domain.enums import operation_results

router = APIRouter()


@router.post(
    "/refresh",
    response_model=auth_contracts.TokenResponse,
    responses={
        status.HTTP_200_OK: {"description": "Token refreshed successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh_token(
    refresh_token_request: auth_contracts.RefreshTokenRequest, use_case: Injected[RefreshTokenUseCase]
) -> auth_contracts.TokenResponse:
    """Issue a new access and refresh token pair from a valid refresh token.

    Raises:
        HTTPException: 401 if the refresh token is invalid or expired, 500
            for an unexpected failure.
    """
    result, token_response = await use_case.execute(refresh_token_request.refresh_token)

    if result == operation_results.LoginResult.SUCCESS and token_response is not None:
        return token_response

    if result == operation_results.LoginResult.INVALID_CREDENTIALS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token", headers={"WWW-Authenticate": "Bearer"}
        )

    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token refresh failed")
