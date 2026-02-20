from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi_injector import Injected

from src.api.routers.greeting.greeting_converter import GreetingConverter
from src.api.routers.greeting.greeting_schema import GreetingCreateRequest, GreetingResponse, HelloWorldResponse
from src.api.result_status_maps import create_response, delete_response
from src.api.schemas.operation_schema import CreateOperationResponse, DeleteOperationResponse
from src.application.use_cases.greeting.greeting_use_case_base import GreetingUseCaseBase

router = APIRouter(prefix="/api/v1", tags=["greetings"])


@router.get("/hello", response_model=HelloWorldResponse)
async def hello_world() -> HelloWorldResponse:
    """Return a hello world message with the current timestamp.

    Returns:
        A HelloWorldResponse containing the greeting message and timestamp.
    """
    return HelloWorldResponse(
        message="Hello, World!",
        timestamp=datetime.utcnow(),
    )


@router.post(
    "/greetings",
    response_model=CreateOperationResponse,
    responses={
        status.HTTP_201_CREATED: {"description": "Greeting created successfully"},
        status.HTTP_409_CONFLICT: {"description": "Unique constraint violation or concurrency conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Unexpected failure"},
    },
)
async def create_greeting(
    greeting_data: GreetingCreateRequest,
    use_case: GreetingUseCaseBase = Injected(GreetingUseCaseBase),
) -> JSONResponse:
    """Create a new greeting.

    Args:
        greeting_data: The request body containing the greeting message.
        use_case: The injected greeting use case for business logic.

    Returns:
        A CreateOperationResponse with the result enum and the new greeting id on success.
    """
    create_greeting_dto = GreetingConverter.to_create_dto(greeting_data)
    result, entity_id = await use_case.create_greeting(create_greeting_dto)
    return create_response(result, entity_id)


@router.get("/greetings/{greeting_id}", response_model=GreetingResponse)
async def get_greeting(
    greeting_id: int,
    use_case: GreetingUseCaseBase = Injected(GreetingUseCaseBase),
) -> GreetingResponse:
    """Get a greeting by its unique identifier.

    Args:
        greeting_id: The unique identifier of the greeting to retrieve.
        use_case: The injected greeting use case for business logic.

    Returns:
        A GreetingResponse representing the found greeting.

    Raises:
        HTTPException: 404 if the greeting is not found.
    """
    greeting_dto = await use_case.get_greeting(greeting_id)

    if greeting_dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Greeting with id {greeting_id} not found",
        )

    return GreetingConverter.to_response(greeting_dto)


@router.get("/greetings", response_model=list[GreetingResponse])
async def get_all_greetings(
    use_case: GreetingUseCaseBase = Injected(GreetingUseCaseBase),
) -> list[GreetingResponse]:
    """Get all greetings.

    Args:
        use_case: The injected greeting use case for business logic.

    Returns:
        A list of GreetingResponse representing all greetings.
    """
    greeting_list_dto = await use_case.get_all_greetings()
    return GreetingConverter.to_response_list(greeting_list_dto)


@router.delete(
    "/greetings/{greeting_id}",
    response_model=DeleteOperationResponse,
    responses={
        status.HTTP_200_OK: {"description": "Greeting deleted successfully"},
        status.HTTP_404_NOT_FOUND: {"description": "Greeting not found"},
        status.HTTP_409_CONFLICT: {"description": "Concurrency conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Unexpected failure"},
    },
)
async def delete_greeting(
    greeting_id: int,
    use_case: GreetingUseCaseBase = Injected(GreetingUseCaseBase),
) -> JSONResponse:
    """Delete a greeting by its unique identifier.

    Args:
        greeting_id: The unique identifier of the greeting to delete.
        use_case: The injected greeting use case for business logic.

    Returns:
        A DeleteOperationResponse with the result enum indicating the outcome.
    """
    result = await use_case.delete_greeting(greeting_id)
    return delete_response(result)
