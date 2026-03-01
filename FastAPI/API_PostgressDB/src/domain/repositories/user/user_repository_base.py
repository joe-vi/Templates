"""Abstract base class for the user repository."""

from abc import ABC, abstractmethod

from src.domain.entities.user import user as user_module
from src.domain.enums import operation_results, user_enum


class UserRepositoryBase(ABC):
    """Abstract base class for user repository."""

    @abstractmethod
    async def create(
        self, user: user_module.User
    ) -> tuple[operation_results.CreateResult, int | None]:
        """Persist a new user entity.

        Args:
            user: The user entity to persist.

        Returns:
            A tuple of (result, id). id is the newly created user id on
            success, None on any failure.
        """
        pass

    @abstractmethod
    async def get_by_id(self, user_id: int) -> user_module.User | None:
        """Retrieve a user entity by its unique identifier.

        Args:
            user_id: The unique identifier of the user to retrieve.

        Returns:
            The User entity if found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_all(self) -> list[user_module.User]:
        """Retrieve all user entities.

        Returns:
            A list of all User entities.
        """
        pass

    @abstractmethod
    async def update_role(
        self, user_id: int, role: user_enum.UserRole
    ) -> operation_results.UpdateResult:
        """Update the role of a user entity.

        Args:
            user_id: The unique identifier of the user to update.
            role: The new role to assign to the user.

        Returns:
            An UpdateResult enum indicating the outcome of the operation.
        """
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> user_module.User | None:
        """Retrieve a user entity by its username.

        Args:
            username: The username of the user to retrieve.

        Returns:
            The User entity if found, None otherwise.
        """
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> operation_results.DeleteResult:
        """Delete a user entity by its unique identifier.

        Args:
            user_id: The unique identifier of the user to delete.

        Returns:
            A DeleteResult enum indicating the outcome of the operation.
        """
        pass
