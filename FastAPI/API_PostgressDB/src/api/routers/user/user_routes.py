from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi_injector import Injected

from src.api.routers.user.user_converter import UserConverter
from src.api.routers.user.user_schema import UserCreateRequest, UserResponse, UserUpdateRoleRequest
from src.api.result_status_maps import create_response, delete_response, update_response
from src.api.schemas.operation_schema import CreateOperationResponse, DeleteOperationResponse, UpdateOperationResponse
from src.application.use_cases.user.user_use_case_base import UserUseCaseBase

router = APIRouter(prefix="/api/v1", tags=["users"])


@router.post(
    "/users",
    response_model=CreateOperationResponse,
    responses={
        status.HTTP_201_CREATED: {"description": "User created successfully"},
        status.HTTP_409_CONFLICT: {"description": "Unique constraint violation or concurrency conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Unexpected failure"},
    },
)
async def create_user(
    user_data: UserCreateRequest,
    use_case: UserUseCaseBase = Injected(UserUseCaseBase),
) -> JSONResponse:
    """Create a new user.

    Args:
        user_data: The request body containing the user data.
        use_case: The injected user use case for business logic.

    Returns:
        A CreateOperationResponse with the result enum and the new user id on success.
    """
    create_user_dto = UserConverter.to_create_dto(user_data)
    result, entity_id = await use_case.create_user(create_user_dto)
    return create_response(result, entity_id)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    use_case: UserUseCaseBase = Injected(UserUseCaseBase),
) -> UserResponse:
    """Get a user by its unique identifier.

    Args:
        user_id: The unique identifier of the user to retrieve.
        use_case: The injected user use case for business logic.

    Returns:
        A UserResponse representing the found user.

    Raises:
        HTTPException: 404 if the user is not found.
    """
    user_dto = await use_case.get_user(user_id)

    if user_dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )

    return UserConverter.to_response(user_dto)


@router.get("/users", response_model=list[UserResponse])
async def get_all_users(
    use_case: UserUseCaseBase = Injected(UserUseCaseBase),
) -> list[UserResponse]:
    """Get all users.

    Args:
        use_case: The injected user use case for business logic.

    Returns:
        A list of UserResponse representing all users.
    """
    user_list_dto = await use_case.get_all_users()
    return UserConverter.to_response_list(user_list_dto)


@router.patch(
    "/users/{user_id}/role",
    response_model=UpdateOperationResponse,
    responses={
        status.HTTP_200_OK: {"description": "User role updated successfully"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_409_CONFLICT: {"description": "Concurrency conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Unexpected failure"},
    },
)
async def update_user_role(
    user_id: int,
    role_data: UserUpdateRoleRequest,
    use_case: UserUseCaseBase = Injected(UserUseCaseBase),
) -> JSONResponse:
    """Update the role of a user.

    Args:
        user_id: The unique identifier of the user to update.
        role_data: The request body containing the new role.
        use_case: The injected user use case for business logic.

    Returns:
        An UpdateOperationResponse with the result enum indicating the outcome.
    """
    update_user_role_dto = UserConverter.to_update_role_dto(user_id, role_data)
    result = await use_case.update_user_role(update_user_role_dto)
    return update_response(result)


@router.delete(
    "/users/{user_id}",
    response_model=DeleteOperationResponse,
    responses={
        status.HTTP_200_OK: {"description": "User deleted successfully"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_409_CONFLICT: {"description": "Concurrency conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Unexpected failure"},
    },
)
async def delete_user(
    user_id: int,
    use_case: UserUseCaseBase = Injected(UserUseCaseBase),
) -> JSONResponse:
    """Delete a user by its unique identifier.

    Args:
        user_id: The unique identifier of the user to delete.
        use_case: The injected user use case for business logic.

    Returns:
        A DeleteOperationResponse with the result enum indicating the outcome.
    """
    result = await use_case.delete_user(user_id)
    return delete_response(result)
