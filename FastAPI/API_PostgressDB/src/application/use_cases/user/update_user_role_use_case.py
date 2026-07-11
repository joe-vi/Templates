from injector import inject

from src.application.services.transaction_context import TransactionContext
from src.application.use_cases.user import user_dto
from src.domain.enums import operation_results
from src.domain.repositories.user.user_repository import UserRepository


class UpdateUserRoleUseCase:
    """Assigns a new role to a user."""

    @inject
    def __init__(self, repository: UserRepository, transaction_context: TransactionContext) -> None:
        self._repository = repository
        self._transaction_context = transaction_context

    async def execute(self, update_user_role_dto: user_dto.UpdateUserRoleDTO) -> operation_results.UpdateResult:
        """Assign a new role to a user.

        Args:
            update_user_role_dto: The target user id and the role to assign.

        Returns:
            An UpdateResult describing the outcome.
        """
        async with self._transaction_context.begin() as transaction:
            result = await self._repository.update_role(update_user_role_dto.user_id, update_user_role_dto.role)
            if result == operation_results.UpdateResult.SUCCESS:
                await transaction.commit()
        return result
