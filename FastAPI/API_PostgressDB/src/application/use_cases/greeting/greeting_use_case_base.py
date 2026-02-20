from abc import ABC, abstractmethod

from src.application.use_cases.greeting.greeting_dto import CreateGreetingDTO, GreetingDTO
from src.domain.enums.operation_results import CreateResult, DeleteResult


class GreetingUseCaseBase(ABC):
    """Abstract base class for greeting use case."""

    @abstractmethod
    async def create_greeting(self, create_greeting_dto: CreateGreetingDTO) -> tuple[CreateResult, int | None]:
        """Create a new greeting.

        Args:
            create_greeting_dto: The DTO containing the greeting data to create.

        Returns:
            A tuple of (result, entity_id). entity_id is the newly created greeting id on success, None otherwise.
        """
        pass

    @abstractmethod
    async def get_greeting(self, greeting_id: int) -> GreetingDTO | None:
        """Get a greeting by its unique identifier.

        Args:
            greeting_id: The unique identifier of the greeting to retrieve.

        Returns:
            A GreetingDTO if the greeting is found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_all_greetings(self) -> list[GreetingDTO]:
        """Get all greetings.

        Returns:
            A list of GreetingDTOs.
        """
        pass

    @abstractmethod
    async def delete_greeting(self, greeting_id: int) -> DeleteResult:
        """Delete a greeting by its unique identifier.

        Args:
            greeting_id: The unique identifier of the greeting to delete.

        Returns:
            A DeleteResult enum indicating the outcome of the deletion.
        """
        pass
