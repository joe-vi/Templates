from src.api.schemas.greeting_schema import (
    GreetingCreateRequest,
    GreetingResponse,
)
from src.application.dtos.greeting_dto import (
    CreateGreetingDTO,
    GreetingDTO,
    GreetingListDTO,
)


class GreetingConverter:
    """Converts between API request/response models and application DTOs."""

    @staticmethod
    def to_create_dto(request: GreetingCreateRequest) -> CreateGreetingDTO:
        """Convert a create greeting request to a DTO for the application layer.

        Args:
            request: The API request containing the greeting creation data.

        Returns:
            A CreateGreetingDTO populated with data from the request.
        """
        return CreateGreetingDTO(message=request.message)

    @staticmethod
    def to_response(greeting_dto: GreetingDTO) -> GreetingResponse:
        """Convert a greeting DTO to an API response model.

        Args:
            greeting_dto: The application DTO containing greeting data.

        Returns:
            A GreetingResponse populated with data from the DTO.
        """
        return GreetingResponse(
            id=greeting_dto.id,
            message=greeting_dto.message,
            created_at=greeting_dto.created_at,
        )

    @staticmethod
    def to_response_list(greeting_list_dto: GreetingListDTO) -> list[GreetingResponse]:
        """Convert a greeting list DTO to a list of API response models.

        Args:
            greeting_list_dto: The application DTO containing a collection of greetings.

        Returns:
            A list of GreetingResponse models, one per greeting in the DTO.
        """
        return [GreetingConverter.to_response(greeting_dto) for greeting_dto in greeting_list_dto.greetings]
