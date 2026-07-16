from injector import inject

from src.domain.enums import operation_results
from src.domain.repositories.user.user_repository import UserRepository
from src.ports.transaction_context import TransactionContext


class DeleteUserUseCase:
    """Deletes a user."""

    @inject
    def __init__(self, repository: UserRepository, transaction_context: TransactionContext) -> None:
        self._repository = repository
        self._transaction_context = transaction_context

    async def execute(self, user_id: int) -> operation_results.DeleteResult:
        """Delete the user with the given id.

        Args:
            user_id: The unique identifier of the user to delete.

        Returns:
            A DeleteResult describing the outcome.
        """
        async with self._transaction_context.begin() as transaction:
            result = await self._repository.delete(user_id)
            if result == operation_results.DeleteResult.SUCCESS:
                await transaction.commit()
        return result
