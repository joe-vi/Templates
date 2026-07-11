from typing import Protocol

from src.domain.entities.user.user import User
from src.domain.enums import operation_results, user_enum


class UserRepository(Protocol):
    """Persistence port for the ``User`` aggregate.

    One repository per aggregate root. Adapters subclass this protocol
    explicitly, so the documented contract below is inherited — the method
    docstrings here are the single source of documentation for every
    implementation, and IDEs surface them on hover at both the call site and
    inside the adapter.

    Mutation methods never raise for expected database failures; they map them
    to the shared operation result enums. They also never commit — the
    transaction boundary belongs to the use case via ``TransactionContext``.
    """

    async def create(self, user: User) -> tuple[operation_results.CreateResult, int | None]:
        """Persist a new user aggregate.

        Args:
            user: The unpersisted user entity (``id`` must be None).

        Returns:
            A tuple of (result, id): the newly created user id on success,
            None on any failure result.
        """
        ...

    async def get_by_id(self, user_id: int) -> User | None:
        """Load a user by its unique identifier.

        Args:
            user_id: The unique identifier of the user to load.

        Returns:
            The User entity if found, None otherwise.
        """
        ...

    async def get_all(self) -> list[User]:
        """Load all users.

        Returns:
            All User entities; an empty list when there are none.
        """
        ...

    async def get_by_username(self, username: str) -> User | None:
        """Load a user by its unique username.

        Args:
            username: The username of the user to load.

        Returns:
            The User entity if found, None otherwise.
        """
        ...

    async def update_role(self, user_id: int, role: user_enum.UserRole) -> operation_results.UpdateResult:
        """Assign a new role to the user with the given id.

        A targeted single-column update: it does not load the aggregate and
        reports ``NOT_FOUND`` when no row matched.

        Args:
            user_id: The unique identifier of the user to update.
            role: The role to assign.

        Returns:
            An UpdateResult describing the outcome.
        """
        ...

    async def delete(self, user_id: int) -> operation_results.DeleteResult:
        """Delete the user with the given id.

        Args:
            user_id: The unique identifier of the user to delete.

        Returns:
            A DeleteResult describing the outcome; ``NOT_FOUND`` when no row
            matched.
        """
        ...
