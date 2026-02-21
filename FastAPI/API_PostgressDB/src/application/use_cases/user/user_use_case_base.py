from abc import ABC, abstractmethod

from src.application.use_cases.user.user_dto import CreateUserDTO, UpdateUserRoleDTO, UserDTO
from src.domain.enums.operation_results import CreateResult, DeleteResult, UpdateResult


class UserUseCaseBase(ABC):
    """Abstract base class for user use case."""

    @abstractmethod
    async def create_user(self, create_user_dto: CreateUserDTO) -> tuple[CreateResult, int | None]:
        """Create a new user.

        Args:
            create_user_dto: The DTO containing the user data to create.

        Returns:
            A tuple of (result, entity_id). entity_id is the newly created user id on success, None otherwise.
        """
        pass

    @abstractmethod
    async def get_user(self, user_id: int) -> UserDTO | None:
        """Get a user by its unique identifier.

        Args:
            user_id: The unique identifier of the user to retrieve.

        Returns:
            A UserDTO if the user is found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_all_users(self) -> list[UserDTO]:
        """Get all users.

        Returns:
            A list of UserDTOs.
        """
        pass

    @abstractmethod
    async def update_user_role(self, update_user_role_dto: UpdateUserRoleDTO) -> UpdateResult:
        """Update the role of an existing user.

        Args:
            update_user_role_dto: The DTO containing the user id and the new role.

        Returns:
            An UpdateResult enum indicating the outcome of the update.
        """
        pass

    @abstractmethod
    async def delete_user(self, user_id: int) -> DeleteResult:
        """Delete a user by its unique identifier.

        Args:
            user_id: The unique identifier of the user to delete.

        Returns:
            A DeleteResult enum indicating the outcome of the deletion.
        """
        pass
