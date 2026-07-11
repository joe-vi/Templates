from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Response, status

from src.api import result_status_maps
from src.api.dependencies.injected import Injected
from src.api.dependencies.jwt_dependency import get_current_user
from src.api.schemas import operation_schema
from src.application.use_cases.user import user_dto
from src.application.use_cases.user.user_use_case import UserUseCase
from src.domain.enums import user_enum

router = APIRouter(prefix="/api/v1", tags=["users"], dependencies=[Depends(get_current_user)])

UseCaseDep = Annotated[UserUseCase, Injected(UserUseCase)]


@router.post(
    "/users",
    response_model=operation_schema.CreateOperationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "User created successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Missing or invalid JWT token"},
        status.HTTP_409_CONFLICT: {"description": "Unique constraint violation or concurrency conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Unexpected failure"},
    },
)
async def create_user(
    create_user_dto: user_dto.CreateUserDTO, response: Response, use_case: UseCaseDep
) -> operation_schema.CreateOperationResponse:
    """Create a new user.

    Returns a CreateOperationResponse whose result enum and HTTP status
    reflect the outcome; the new user id is set on success.
    """
    result, entity_id = await use_case.create_user(create_user_dto)
    response.status_code = result_status_maps.CREATE_STATUS_MAP[result]
    return operation_schema.CreateOperationResponse(result=result, message=result_status_maps.CREATE_MESSAGE_MAP[result], id=entity_id)


@router.get(
    "/users/{user_id}",
    response_model=user_dto.UserDTO,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Missing or invalid JWT token"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
async def get_user(user_id: int, use_case: UseCaseDep) -> user_dto.UserDTO:
    """Get a user by its unique identifier.

    Raises:
        HTTPException: 404 if the user is not found.
    """
    found_user = await use_case.get_user(user_id)

    if found_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {user_id} not found")

    return found_user


@router.get(
    "/users",
    response_model=list[user_dto.UserDTO],
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Missing or invalid JWT token"}},
)
async def get_all_users(use_case: UseCaseDep) -> list[user_dto.UserDTO]:
    """Get all users."""
    return await use_case.get_all_users()


@router.patch(
    "/users/{user_id}/role",
    response_model=operation_schema.UpdateOperationResponse,
    responses={
        status.HTTP_200_OK: {"description": "User role updated successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Missing or invalid JWT token"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_409_CONFLICT: {"description": "Concurrency conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Unexpected failure"},
    },
)
async def update_user_role(
    user_id: int,
    role: Annotated[user_enum.UserRole, Body(embed=True, description="The new role to assign to the user")],
    response: Response,
    use_case: UseCaseDep,
) -> operation_schema.UpdateOperationResponse:
    """Update the role of a user.

    The user id comes from the path and the role from the request body
    (``{"role": ...}``); the two are combined into the use-case DTO here.
    """
    update_user_role_dto = user_dto.UpdateUserRoleDTO(user_id=user_id, role=role)
    result = await use_case.update_user_role(update_user_role_dto)
    response.status_code = result_status_maps.UPDATE_STATUS_MAP[result]
    return operation_schema.UpdateOperationResponse(result=result, message=result_status_maps.UPDATE_MESSAGE_MAP[result])


@router.delete(
    "/users/{user_id}",
    response_model=operation_schema.DeleteOperationResponse,
    responses={
        status.HTTP_200_OK: {"description": "User deleted successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Missing or invalid JWT token"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_409_CONFLICT: {"description": "Concurrency conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Unexpected failure"},
    },
)
async def delete_user(user_id: int, response: Response, use_case: UseCaseDep) -> operation_schema.DeleteOperationResponse:
    """Delete a user by its unique identifier."""
    result = await use_case.delete_user(user_id)
    response.status_code = result_status_maps.DELETE_STATUS_MAP[result]
    return operation_schema.DeleteOperationResponse(result=result, message=result_status_maps.DELETE_MESSAGE_MAP[result])
