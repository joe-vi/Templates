from src.application.use_cases.greeting.greeting_dto import CreateGreetingDTO, GreetingDTO
from src.domain.entities.greeting.greeting import Greeting


class GreetingEntityConverter:
    """Converts between domain entities and DTOs."""

    @staticmethod
    def to_dto(greeting: Greeting) -> GreetingDTO:
        """Convert a domain greeting entity to a DTO.

        Args:
            greeting: The domain entity to convert.

        Returns:
            A GreetingDTO populated with the entity's data.
        """
        return GreetingDTO(
            id=greeting.id,  # type: ignore
            message=greeting.message,
            status=greeting.status,
            created_at=greeting.created_at,  # type: ignore
        )

    @staticmethod
    def to_dto_list(greetings: list[Greeting]) -> list[GreetingDTO]:
        """Convert a list of domain greeting entities to a list of DTOs.

        Args:
            greetings: The list of domain entities to convert.

        Returns:
            A list of GreetingDTOs.
        """
        return [GreetingEntityConverter.to_dto(greeting) for greeting in greetings]

    @staticmethod
    def to_entity(create_greeting_dto: CreateGreetingDTO) -> Greeting:
        """Convert a creation DTO to a domain greeting entity.

        Args:
            create_greeting_dto: The DTO containing data for the new greeting.

        Returns:
            A new Greeting entity with id set to None.
        """
        return Greeting(
            id=None,
            message=create_greeting_dto.message,
            status=create_greeting_dto.status,
        )
