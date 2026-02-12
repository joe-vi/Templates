from abc import ABC, abstractmethod

from src.application.dtos.greeting_dto import (
    CreateGreetingDTO,
    DeleteResultDTO,
    GreetingDTO,
    GreetingListDTO,
)


class GreetingUseCaseBase(ABC):
    """Abstract base class for greeting use case."""

    @abstractmethod
    async def create_greeting(self, create_greeting_dto: CreateGreetingDTO) -> GreetingDTO:
        """Create a new greeting.

        Args:
            create_greeting_dto: The DTO containing the greeting data to create.

        Returns:
            A GreetingDTO representing the newly created greeting.
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
    async def get_all_greetings(self) -> GreetingListDTO:
        """Get all greetings.

        Returns:
            A GreetingListDTO containing all greetings.
        """
        pass

    @abstractmethod
    async def delete_greeting(self, greeting_id: int) -> DeleteResultDTO:
        """Delete a greeting by its unique identifier.

        Args:
            greeting_id: The unique identifier of the greeting to delete.

        Returns:
            A DeleteResultDTO indicating whether the deletion was successful.
        """
        pass
