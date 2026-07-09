"""User use case."""

from injector import inject

from src.application.services.password_hasher import PasswordHasher
from src.application.services.transaction_context import TransactionContext
from src.application.use_cases.user import user_converter, user_dto
from src.domain.enums import operation_results
from src.domain.repositories.user.user_repository import UserRepository


class UserUseCase:
    """Application logic for user operations.

    Depends only on ports; the concrete adapters are supplied by the API
    dependency providers. Mutations run inside a ``TransactionContext``
    block and commit only on success — a use case orchestrating several
    repositories wraps all of their calls in one block so they succeed or
    fail together.
    """

    @inject
    def __init__(
        self,
        repository: UserRepository,
        password_hasher: PasswordHasher,
        transaction_context: TransactionContext,
    ) -> None:
        """Initialize the user use case.

        Args:
            repository: The user repository port for persistence.
            password_hasher: The port for hashing plain-text passwords.
            transaction_context: The port owning commit/rollback for
                mutating operations.
        """
        self._repository = repository
        self._password_hasher = password_hasher
        self._transaction_context = transaction_context

    async def create_user(
        self, create_user_dto: user_dto.CreateUserDTO
    ) -> tuple[operation_results.CreateResult, int | None]:
        """Create a new user."""
        hashed_password = self._password_hasher.hash(create_user_dto.password)
        user = user_converter.to_entity(create_user_dto, hashed_password)

        async with self._transaction_context.begin() as transaction:
            result, user_id = await self._repository.create(user)
            if result == operation_results.CreateResult.SUCCESS:
                await transaction.commit()
        return (result, user_id)

    async def get_user(self, user_id: int) -> user_dto.UserDTO | None:
        """Return the user with the given id, or None if absent."""
        user = await self._repository.get_by_id(user_id)

        if user is None:
            return None

        return user_converter.to_dto(user)

    async def get_all_users(self) -> list[user_dto.UserDTO]:
        """Return all users as DTOs."""
        users = await self._repository.get_all()
        return user_converter.to_dto_list(users)

    async def update_user_role(
        self, update_user_role_dto: user_dto.UpdateUserRoleDTO
    ) -> operation_results.UpdateResult:
        """Update a user's role."""
        async with self._transaction_context.begin() as transaction:
            result = await self._repository.update_role(
                update_user_role_dto.user_id, update_user_role_dto.role
            )
            if result == operation_results.UpdateResult.SUCCESS:
                await transaction.commit()
        return result

    async def delete_user(self, user_id: int) -> operation_results.DeleteResult:
        """Delete the user with the given id."""
        async with self._transaction_context.begin() as transaction:
            result = await self._repository.delete(user_id)
            if result == operation_results.DeleteResult.SUCCESS:
                await transaction.commit()
        return result
