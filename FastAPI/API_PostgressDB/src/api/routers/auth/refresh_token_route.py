from typing import Annotated

from fastapi import APIRouter, HTTPException, status

from src.api.dependencies.injected import Injected
from src.application.use_cases.auth import auth_dto
from src.application.use_cases.auth.refresh_token_use_case import RefreshTokenUseCase
from src.domain.enums import operation_results

router = APIRouter()

UseCaseDep = Annotated[RefreshTokenUseCase, Injected(RefreshTokenUseCase)]


@router.post(
    "/refresh",
    response_model=auth_dto.TokenDTO,
    responses={
        status.HTTP_200_OK: {"description": "Token refreshed successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh_token(refresh_token_dto: auth_dto.RefreshTokenDTO, use_case: UseCaseDep) -> auth_dto.TokenDTO:
    """Issue a new access and refresh token pair from a valid refresh token.

    Raises:
        HTTPException: 401 if the refresh token is invalid or expired, 500
            for an unexpected failure.
    """
    result, token_dto = await use_case.execute(refresh_token_dto.refresh_token)

    if result == operation_results.LoginResult.SUCCESS and token_dto is not None:
        return token_dto

    if result == operation_results.LoginResult.INVALID_CREDENTIALS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token", headers={"WWW-Authenticate": "Bearer"}
        )

    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token refresh failed")
