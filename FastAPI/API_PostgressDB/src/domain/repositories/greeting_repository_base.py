from abc import ABC, abstractmethod

from src.domain.entities.greeting import Greeting


class GreetingRepositoryBase(ABC):
    """Abstract base class for greeting repository."""

    @abstractmethod
    async def create(self, greeting: Greeting) -> Greeting:
        """Persist a new greeting entity.

        Args:
            greeting: The greeting entity to persist.

        Returns:
            The persisted Greeting entity with generated id and timestamps.
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
    async def delete(self, greeting_id: int) -> bool:
        """Delete a greeting entity by its unique identifier.

        Args:
            greeting_id: The unique identifier of the greeting to delete.

        Returns:
            True if the greeting was deleted, False if it was not found.
        """
        pass
