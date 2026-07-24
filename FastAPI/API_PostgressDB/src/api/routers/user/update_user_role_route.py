from typing import Annotated

from fastapi import APIRouter, Body, Response, status

from src.api import result_status_maps
from src.api.dependencies.injected import Injected
from src.api.schemas import operation_schema
from src.application.use_cases.user.update_user_role_use_case import UpdateUserRoleUseCase
from src.domain.enums import user_enum

router = APIRouter()


@router.patch(
    "/{user_id}/role",
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
    use_case: Injected[UpdateUserRoleUseCase],
) -> operation_schema.UpdateOperationResponse:
    """Update the role of a user."""
    result = await use_case.execute(user_id, role)
    response.status_code = result_status_maps.UPDATE_STATUS_MAP[result]
    return operation_schema.UpdateOperationResponse(result=result, message=result_status_maps.UPDATE_MESSAGE_MAP[result])
