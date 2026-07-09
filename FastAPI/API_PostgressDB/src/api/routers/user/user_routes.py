"""API routes for user CRUD operations."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from src.api import result_status_maps
from src.api.dependencies.injection import Injected
from src.api.dependencies.jwt_dependency import get_current_user
from src.api.routers.user import user_converter, user_schema
from src.api.schemas import operation_schema
from src.application.use_cases.user.user_use_case import UserUseCase

router = APIRouter(
    prefix="/api/v1",
    tags=["users"],
    dependencies=[Depends(get_current_user)],
)

UseCaseDep = Annotated[UserUseCase, Injected(UserUseCase)]


@router.post(
    "/users",
    response_model=operation_schema.CreateOperationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "User created successfully"},
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Missing or invalid JWT token"
        },
        status.HTTP_409_CONFLICT: {
            "description": "Unique constraint violation or concurrency conflict"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Unexpected failure"
        },
    },
)
async def create_user(
    user_data: user_schema.UserCreateRequest,
    response: Response,
    use_case: UseCaseDep,
) -> operation_schema.CreateOperationResponse:
    """Create a new user.

    Args:
        user_data: The request body containing the user data.
        response: The response object, used to set the result status code.
        use_case: The injected user use case.

    Returns:
        A CreateOperationResponse with the result enum and new user id.
    """
    create_user_dto = user_converter.to_create_dto(user_data)
    result, entity_id = await use_case.create_user(create_user_dto)
    response.status_code = result_status_maps.CREATE_STATUS_MAP[result]
    return operation_schema.CreateOperationResponse(
        result=result,
        message=result_status_maps.CREATE_MESSAGE_MAP[result],
        id=entity_id,
    )


@router.get(
    "/users/{user_id}",
    response_model=user_schema.UserResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Missing or invalid JWT token"
        },
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
async def get_user(
    user_id: int,
    use_case: UseCaseDep,
) -> user_schema.UserResponse:
    """Get a user by its unique identifier.

    Args:
        user_id: The unique identifier of the user to retrieve.
        use_case: The injected user use case.

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

    return user_converter.to_response(user_dto)


@router.get(
    "/users",
    response_model=list[user_schema.UserResponse],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Missing or invalid JWT token"
        },
    },
)
async def get_all_users(
    use_case: UseCaseDep,
) -> list[user_schema.UserResponse]:
    """Get all users.

    Args:
        use_case: The injected user use case.

    Returns:
        A list of UserResponse representing all users.
    """
    user_list_dto = await use_case.get_all_users()
    return user_converter.to_response_list(user_list_dto)


@router.patch(
    "/users/{user_id}/role",
    response_model=operation_schema.UpdateOperationResponse,
    responses={
        status.HTTP_200_OK: {"description": "User role updated successfully"},
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Missing or invalid JWT token"
        },
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_409_CONFLICT: {"description": "Concurrency conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Unexpected failure"
        },
    },
)
async def update_user_role(
    user_id: int,
    role_data: user_schema.UserUpdateRoleRequest,
    response: Response,
    use_case: UseCaseDep,
) -> operation_schema.UpdateOperationResponse:
    """Update the role of a user.

    Args:
        user_id: The unique identifier of the user to update.
        role_data: The request body containing the new role.
        response: The response object, used to set the result status code.
        use_case: The injected user use case.

    Returns:
        An UpdateOperationResponse with the result enum indicating the outcome.
    """
    update_user_role_dto = user_converter.to_update_role_dto(user_id, role_data)
    result = await use_case.update_user_role(update_user_role_dto)
    response.status_code = result_status_maps.UPDATE_STATUS_MAP[result]
    return operation_schema.UpdateOperationResponse(
        result=result,
        message=result_status_maps.UPDATE_MESSAGE_MAP[result],
    )


@router.delete(
    "/users/{user_id}",
    response_model=operation_schema.DeleteOperationResponse,
    responses={
        status.HTTP_200_OK: {"description": "User deleted successfully"},
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Missing or invalid JWT token"
        },
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_409_CONFLICT: {"description": "Concurrency conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Unexpected failure"
        },
    },
)
async def delete_user(
    user_id: int,
    response: Response,
    use_case: UseCaseDep,
) -> operation_schema.DeleteOperationResponse:
    """Delete a user by its unique identifier.

    Args:
        user_id: The unique identifier of the user to delete.
        response: The response object, used to set the result status code.
        use_case: The injected user use case.

    Returns:
        A DeleteOperationResponse with the result enum indicating the outcome.
    """
    result = await use_case.delete_user(user_id)
    response.status_code = result_status_maps.DELETE_STATUS_MAP[result]
    return operation_schema.DeleteOperationResponse(
        result=result,
        message=result_status_maps.DELETE_MESSAGE_MAP[result],
    )
