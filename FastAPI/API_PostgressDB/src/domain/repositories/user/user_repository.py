"""User repository port (structural interface)."""

from typing import Protocol

from src.domain.entities.user.user import User
from src.domain.enums import operation_results, user_enum


class UserRepository(Protocol):
    """Port for user persistence.

    A ``typing.Protocol`` rather than an ABC: implementations satisfy it
    structurally and do not need to import or subclass it, keeping the
    dependency pointing inward without coupling the adapter to the port.
    """

    async def create(
        self, user: User
    ) -> tuple[operation_results.CreateResult, int | None]:
        """Persist a new user entity.

        Args:
            user: The user entity to persist.

        Returns:
            A tuple of (result, id). id is the newly created user id on
            success, None on any failure.
        """
        ...

    async def get_by_id(self, user_id: int) -> User | None:
        """Retrieve a user entity by its unique identifier.

        Args:
            user_id: The unique identifier of the user to retrieve.

        Returns:
            The User entity if found, None otherwise.
        """
        ...

    async def get_all(self) -> list[User]:
        """Retrieve all user entities.

        Returns:
            A list of all User entities.
        """
        ...

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
        ...

    async def get_by_username(self, username: str) -> User | None:
        """Retrieve a user entity by its username.

        Args:
            username: The username of the user to retrieve.

        Returns:
            The User entity if found, None otherwise.
        """
        ...

    async def delete(self, user_id: int) -> operation_results.DeleteResult:
        """Delete a user entity by its unique identifier.

        Args:
            user_id: The unique identifier of the user to delete.

        Returns:
            A DeleteResult enum indicating the outcome of the operation.
        """
        ...
