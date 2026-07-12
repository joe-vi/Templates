from typing import Annotated

from fastapi import APIRouter, HTTPException, status

from src.api.dependencies.injected import Injected
from src.application.use_cases.auth import auth_dto
from src.application.use_cases.auth.login_use_case import LoginUseCase
from src.domain.enums import operation_results

router = APIRouter()

UseCaseDep = Annotated[LoginUseCase, Injected(LoginUseCase)]


@router.post(
    "/login",
    response_model=auth_dto.TokenDTO,
    responses={
        status.HTTP_200_OK: {"description": "Authentication successful"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid credentials"},
        status.HTTP_403_FORBIDDEN: {"description": "User account is inactive"},
    },
)
async def login(login_dto: auth_dto.LoginDTO, use_case: UseCaseDep) -> auth_dto.TokenDTO:
    """Authenticate a user and return a JWT access and refresh token pair.

    The tokens embed the user's id and role as claims.

    Raises:
        HTTPException: 401 for invalid credentials, 403 for an inactive
            account, 500 for an unexpected failure.
    """
    result, token_dto = await use_case.execute(login_dto)

    if result == operation_results.LoginResult.SUCCESS and token_dto is not None:
        return token_dto

    if result == operation_results.LoginResult.INVALID_CREDENTIALS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password", headers={"WWW-Authenticate": "Bearer"}
        )

    if result == operation_results.LoginResult.USER_INACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")
