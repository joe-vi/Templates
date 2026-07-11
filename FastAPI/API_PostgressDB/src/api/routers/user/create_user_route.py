from typing import Annotated

from fastapi import APIRouter, Response, status

from src.api import result_status_maps
from src.api.dependencies.injected import Injected
from src.api.schemas import operation_schema
from src.application.use_cases.user import user_dto
from src.application.use_cases.user.create_user_use_case import CreateUserUseCase

router = APIRouter()

UseCaseDep = Annotated[CreateUserUseCase, Injected(CreateUserUseCase)]


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
    """Create a new user."""
    result, entity_id = await use_case.execute(create_user_dto)
    response.status_code = result_status_maps.CREATE_STATUS_MAP[result]
    return operation_schema.CreateOperationResponse(result=result, message=result_status_maps.CREATE_MESSAGE_MAP[result], id=entity_id)
