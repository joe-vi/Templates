from injector import inject

from src.domain.enums import operation_results, user_enum
from src.domain.repositories.user.user_repository import UserRepository


class UpdateUserRoleUseCase:
    """Assigns a new role to a user."""

    @inject
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self, user_id: int, role: user_enum.UserRole) -> operation_results.UpdateResult:
        """Assign a new role to a user.

        Args:
            user_id: The unique identifier of the target user.
            role: The role to assign.

        Returns:
            An UpdateResult describing the outcome.
        """
        return await self._repository.update_role(user_id, role)
