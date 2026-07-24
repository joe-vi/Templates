from fastapi import APIRouter, HTTPException, status

from src.api.dependencies.injected import Injected
from src.application.use_cases.auth import auth_contracts
from src.application.use_cases.auth.login_use_case import LoginUseCase
from src.domain.enums import operation_results

router = APIRouter()


@router.post(
    "/login",
    response_model=auth_contracts.TokenResponse,
    responses={
        status.HTTP_200_OK: {"description": "Authentication successful"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid credentials"},
        status.HTTP_403_FORBIDDEN: {"description": "User account is inactive"},
    },
)
async def login(login_request: auth_contracts.LoginRequest, use_case: Injected[LoginUseCase]) -> auth_contracts.TokenResponse:
    """Authenticate a user and return a JWT access and refresh token pair.

    Raises:
        HTTPException: 401 for invalid credentials, 403 for an inactive
            account, 500 for an unexpected failure.
    """
    result, token_response = await use_case.execute(login_request)

    if result == operation_results.LoginResult.SUCCESS and token_response is not None:
        return token_response

    if result == operation_results.LoginResult.INVALID_CREDENTIALS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password", headers={"WWW-Authenticate": "Bearer"}
        )

    if result == operation_results.LoginResult.USER_INACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")
