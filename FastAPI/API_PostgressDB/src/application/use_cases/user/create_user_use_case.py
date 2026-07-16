from injector import inject

from src.application.use_cases.user import user_converter, user_dto
from src.domain.enums import operation_results
from src.domain.repositories.user.user_repository import UserRepository
from src.ports.password_hasher import PasswordHasher
from src.ports.transaction_context import TransactionContext


class CreateUserUseCase:
    """Creates a new user."""

    @inject
    def __init__(self, repository: UserRepository, password_hasher: PasswordHasher, transaction_context: TransactionContext) -> None:
        self._repository = repository
        self._password_hasher = password_hasher
        self._transaction_context = transaction_context

    async def execute(self, create_user_dto: user_dto.CreateUserDTO) -> tuple[operation_results.CreateResult, int | None]:
        """Create a new user with a securely hashed password.

        Args:
            create_user_dto: The validated data for the new user.

        Returns:
            A tuple of (result, id): the new user id on success, None on any
            failure result.
        """
        hashed_password = self._password_hasher.hash(create_user_dto.password)
        user = user_converter.to_entity(create_user_dto, hashed_password)

        async with self._transaction_context.begin() as transaction:
            result, user_id = await self._repository.create(user)
            if result == operation_results.CreateResult.SUCCESS:
                await transaction.commit()
        return (result, user_id)
