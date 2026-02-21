from abc import ABC, abstractmethod

from src.domain.entities.user.user import User
from src.domain.enums.operation_results import CreateResult, DeleteResult, UpdateResult
from src.domain.enums.user_enum import UserRole


class UserRepositoryBase(ABC):
    """Abstract base class for user repository."""

    @abstractmethod
    async def create(self, user: User) -> tuple[CreateResult, int | None]:
        """Persist a new user entity.

        Args:
            user: The user entity to persist.

        Returns:
            A tuple of (result, id). id is the newly created user id on success, None on any failure.
        """
        pass

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        """Retrieve a user entity by its unique identifier.

        Args:
            user_id: The unique identifier of the user to retrieve.

        Returns:
            The User entity if found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_all(self) -> list[User]:
        """Retrieve all user entities.

        Returns:
            A list of all User entities.
        """
        pass

    @abstractmethod
    async def update_role(self, user_id: int, role: UserRole) -> UpdateResult:
        """Update the role of a user entity.

        Args:
            user_id: The unique identifier of the user to update.
            role: The new role to assign to the user.

        Returns:
            An UpdateResult enum indicating the outcome of the operation.
        """
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> DeleteResult:
        """Delete a user entity by its unique identifier.

        Args:
            user_id: The unique identifier of the user to delete.

        Returns:
            A DeleteResult enum indicating the outcome of the operation.
        """
        pass
