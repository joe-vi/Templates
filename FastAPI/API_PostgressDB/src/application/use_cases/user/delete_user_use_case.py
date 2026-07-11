from injector import inject

from src.application.services.transaction_context import TransactionContext
from src.domain.enums import operation_results
from src.domain.repositories.user.user_repository import UserRepository


class DeleteUserUseCase:
    """Application logic for deleting a user.

    One use case class per operation. The mutation runs inside a
    ``TransactionContext`` block and commits only on success.
    """

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
