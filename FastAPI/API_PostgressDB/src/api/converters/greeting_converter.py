from src.api.schemas.greeting_schema import (
    GreetingCreateRequest,
    GreetingResponse,
)
from src.application.dtos.greeting_dto import (
    CreateGreetingDTO,
    GreetingDTO,
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
        return CreateGreetingDTO(message=request.message, status=request.status)

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
            status=greeting_dto.status,
            created_at=greeting_dto.created_at,
        )

    @staticmethod
    def to_response_list(greeting_dtos: list[GreetingDTO]) -> list[GreetingResponse]:
        """Convert a list of greeting DTOs to a list of API response models.

        Args:
            greeting_dtos: The list of application DTOs to convert.

        Returns:
            A list of GreetingResponse models, one per DTO.
        """
        return [GreetingConverter.to_response(greeting_dto) for greeting_dto in greeting_dtos]
