from injector import inject

from src.domain.enums import operation_results
from src.domain.repositories.user.user_repository import UserRepository


class DeleteUserUseCase:
    """Deletes a user."""

    @inject
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self, user_id: int) -> operation_results.DeleteResult:
        """Delete the user with the given id.

        Args:
            user_id: The unique identifier of the user to delete.

        Returns:
            A DeleteResult describing the outcome.
        """
        return await self._repository.delete(user_id)
