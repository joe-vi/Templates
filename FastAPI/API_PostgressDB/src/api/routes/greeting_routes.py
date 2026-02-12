from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from fastapi_injector import Injected

from src.api.converters.greeting_converter import GreetingConverter
from src.api.schemas.greeting_schema import (
    GreetingCreateRequest,
    GreetingResponse,
    HelloWorldResponse,
)
from src.application.use_cases.greeting_use_case_base import GreetingUseCaseBase

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
    response_model=GreetingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_greeting(
    greeting_data: GreetingCreateRequest,
    use_case: GreetingUseCaseBase = Injected(GreetingUseCaseBase),
) -> GreetingResponse:
    """Create a new greeting.

    Args:
        greeting_data: The request body containing the greeting message.
        use_case: The injected greeting use case for business logic.

    Returns:
        A GreetingResponse representing the newly created greeting.
    """
    create_greeting_dto = GreetingConverter.to_create_dto(greeting_data)
    created_greeting_dto = await use_case.create_greeting(create_greeting_dto)
    return GreetingConverter.to_response(created_greeting_dto)


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


@router.delete("/greetings/{greeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_greeting(
    greeting_id: int,
    use_case: GreetingUseCaseBase = Injected(GreetingUseCaseBase),
) -> None:
    """Delete a greeting by its unique identifier.

    Args:
        greeting_id: The unique identifier of the greeting to delete.
        use_case: The injected greeting use case for business logic.

    Raises:
        HTTPException: 404 if the greeting is not found.
    """
    delete_result_dto = await use_case.delete_greeting(greeting_id)

    if not delete_result_dto.is_successful:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Greeting with id {greeting_id} not found",
        )
