from fastapi import APIRouter, HTTPException, status

from src.api.dependencies.injected import Injected
from src.application.use_cases.user import user_contracts
from src.application.use_cases.user.get_user_use_case import GetUserUseCase

router = APIRouter()


@router.get(
    "/{user_id}",
    response_model=user_contracts.UserResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Missing or invalid JWT token"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
async def get_user(user_id: int, use_case: Injected[GetUserUseCase]) -> user_contracts.UserResponse:
    """Get a user by its unique identifier.

    Raises:
        HTTPException: 404 if the user is not found.
    """
    found_user = await use_case.execute(user_id)

    if found_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {user_id} not found")

    return found_user
