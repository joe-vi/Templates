from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi_injector import Injected

from src.api.routers.auth.auth_converter import AuthConverter
from src.api.routers.auth.auth_schema import LoginRequest, RefreshTokenRequest, TokenResponse
from src.application.use_cases.auth.auth_use_case_base import AuthUseCaseBase
from src.domain.enums.operation_results import LoginResult

router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    responses={
        status.HTTP_200_OK: {"description": "Authentication successful"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid credentials"},
        status.HTTP_403_FORBIDDEN: {"description": "User account is inactive"},
    },
)
async def login(
    login_data: LoginRequest,
    use_case: AuthUseCaseBase = Injected(AuthUseCaseBase),
) -> JSONResponse:
    """Authenticate a user and return a JWT access and refresh token pair.

    The tokens embed the user's id, username, and role as claims.

    Args:
        login_data: The request body containing username and password.
        use_case: The injected authentication use case.

    Returns:
        A TokenResponse containing the access token, refresh token, and token type.
    """
    login_dto = AuthConverter.to_login_dto(login_data)
    result, token_dto = await use_case.login(login_dto)

    if result == LoginResult.SUCCESS:
        return JSONResponse(content=AuthConverter.to_token_response(token_dto).model_dump())  # type: ignore[arg-type]

    if result == LoginResult.INVALID_CREDENTIALS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if result == LoginResult.USER_INACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")


@router.post(
    "/auth/refresh",
    response_model=TokenResponse,
    responses={
        status.HTTP_200_OK: {"description": "Token refreshed successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    use_case: AuthUseCaseBase = Injected(AuthUseCaseBase),
) -> JSONResponse:
    """Issue a new access and refresh token pair from a valid refresh token.

    Args:
        refresh_data: The request body containing the refresh token.
        use_case: The injected authentication use case.

    Returns:
        A TokenResponse containing the new access token, refresh token, and token type.
    """
    result, token_dto = await use_case.refresh_token(refresh_data.refresh_token)

    if result == LoginResult.SUCCESS:
        return JSONResponse(content=AuthConverter.to_token_response(token_dto).model_dump())  # type: ignore[arg-type]

    if result == LoginResult.INVALID_CREDENTIALS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token refresh failed")
