from injector import inject

from src.domain.enums import operation_results, user_enum
from src.domain.repositories.user.user_repository import UserRepository
from src.ports.transaction_context import TransactionContext


class UpdateUserRoleUseCase:
    """Assigns a new role to a user."""

    @inject
    def __init__(self, repository: UserRepository, transaction_context: TransactionContext) -> None:
        self._repository = repository
        self._transaction_context = transaction_context

    async def execute(self, user_id: int, role: user_enum.UserRole) -> operation_results.UpdateResult:
        """Assign a new role to a user.

        Args:
            user_id: The unique identifier of the target user.
            role: The role to assign.

        Returns:
            An UpdateResult describing the outcome.
        """
        async with self._transaction_context.begin() as transaction:
            result = await self._repository.update_role(user_id, role)
            if result == operation_results.UpdateResult.SUCCESS:
                await transaction.commit()
        return result
