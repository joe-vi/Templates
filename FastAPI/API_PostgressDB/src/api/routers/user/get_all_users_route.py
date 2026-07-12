from typing import Annotated

from fastapi import APIRouter, status

from src.api.dependencies.injected import Injected
from src.application.use_cases.user import user_dto
from src.application.use_cases.user.get_all_users_use_case import GetAllUsersUseCase

router = APIRouter()

UseCaseDep = Annotated[GetAllUsersUseCase, Injected(GetAllUsersUseCase)]


@router.get(
    "/users",
    response_model=list[user_dto.UserDTO],
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Missing or invalid JWT token"}},
)
async def get_all_users(use_case: UseCaseDep) -> list[user_dto.UserDTO]:
    """Get all users."""
    return await use_case.execute()
