"""API routes for authentication operations."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies.providers import get_auth_use_case
from src.api.routers.auth import auth_converter, auth_schema
from src.application.use_cases.auth.auth_use_case import AuthUseCase
from src.domain.enums import operation_results

router = APIRouter(prefix="/api/v1", tags=["auth"])

UseCaseDep = Annotated[AuthUseCase, Depends(get_auth_use_case)]


@router.post(
    "/auth/login",
    response_model=auth_schema.TokenResponse,
    responses={
        status.HTTP_200_OK: {"description": "Authentication successful"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid credentials"},
        status.HTTP_403_FORBIDDEN: {"description": "User account is inactive"},
    },
)
async def login(
    login_data: auth_schema.LoginRequest,
    use_case: UseCaseDep,
) -> auth_schema.TokenResponse:
    """Authenticate a user and return a JWT access and refresh token pair.

    The tokens embed the user's id and role as claims.

    Args:
        login_data: The request body containing username and password.
        use_case: The injected authentication use case.

    Returns:
        A TokenResponse with the access token, refresh token, and token type.
    """
    login_dto = auth_converter.to_login_dto(login_data)
    result, token_dto = await use_case.login(login_dto)

    if result == operation_results.LoginResult.SUCCESS:
        assert token_dto is not None
        return auth_converter.to_token_response(token_dto)

    if result == operation_results.LoginResult.INVALID_CREDENTIALS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if result == operation_results.LoginResult.USER_INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Login failed",
    )


@router.post(
    "/auth/refresh",
    response_model=auth_schema.TokenResponse,
    responses={
        status.HTTP_200_OK: {"description": "Token refreshed successfully"},
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired refresh token"
        },
    },
)
async def refresh_token(
    refresh_data: auth_schema.RefreshTokenRequest,
    use_case: UseCaseDep,
) -> auth_schema.TokenResponse:
    """Issue a new access and refresh token pair from a valid refresh token.

    Args:
        refresh_data: The request body containing the refresh token.
        use_case: The injected authentication use case.

    Returns:
        A TokenResponse with the new access token, refresh token, and type.
    """
    result, token_dto = await use_case.refresh_token(refresh_data.refresh_token)

    if result == operation_results.LoginResult.SUCCESS:
        assert token_dto is not None
        return auth_converter.to_token_response(token_dto)

    if result == operation_results.LoginResult.INVALID_CREDENTIALS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Token refresh failed",
    )
