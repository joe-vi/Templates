from abc import ABC, abstractmethod

from src.domain.entities.greeting import Greeting
from src.domain.enums.operation_results import CreateResult, DeleteResult


class GreetingRepositoryBase(ABC):
    """Abstract base class for greeting repository."""

    @abstractmethod
    async def create(self, greeting: Greeting) -> tuple[CreateResult, int | None]:
        """Persist a new greeting entity.

        Args:
            greeting: The greeting entity to persist.

        Returns:
            A tuple of (result, id). id is the newly created greeting id on success, None on any failure.
        """
        pass

    @abstractmethod
    async def get_by_id(self, greeting_id: int) -> Greeting | None:
        """Retrieve a greeting entity by its unique identifier.

        Args:
            greeting_id: The unique identifier of the greeting to retrieve.

        Returns:
            The Greeting entity if found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_all(self) -> list[Greeting]:
        """Retrieve all greeting entities.

        Returns:
            A list of all Greeting entities.
        """
        pass

    @abstractmethod
    async def delete(self, greeting_id: int) -> DeleteResult:
        """Delete a greeting entity by its unique identifier.

        Args:
            greeting_id: The unique identifier of the greeting to delete.

        Returns:
            A DeleteResult enum indicating the outcome of the operation.
        """
        pass
