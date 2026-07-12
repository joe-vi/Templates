from typing import Annotated

from fastapi import APIRouter, Response, status

from src.api import result_status_maps
from src.api.dependencies.injected import Injected
from src.api.schemas import operation_schema
from src.application.use_cases.user.delete_user_use_case import DeleteUserUseCase

router = APIRouter()

UseCaseDep = Annotated[DeleteUserUseCase, Injected(DeleteUserUseCase)]


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
    result = await use_case.execute(user_id)
    response.status_code = result_status_maps.DELETE_STATUS_MAP[result]
    return operation_schema.DeleteOperationResponse(result=result, message=result_status_maps.DELETE_MESSAGE_MAP[result])
