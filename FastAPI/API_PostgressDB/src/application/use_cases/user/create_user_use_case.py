from injector import inject

from src.application.use_cases.user import user_contracts, user_converter
from src.domain.enums import operation_results
from src.domain.repositories.user.user_repository import UserRepository
from src.ports.password_hasher import PasswordHasher


class CreateUserUseCase:
    """Creates a new user."""

    @inject
    def __init__(self, repository: UserRepository, password_hasher: PasswordHasher) -> None:
        self._repository = repository
        self._password_hasher = password_hasher

    async def execute(self, create_user_request: user_contracts.CreateUserRequest) -> tuple[operation_results.CreateResult, int | None]:
        """Create a new user with a securely hashed password.

        Args:
            create_user_request: The validated data for the new user.

        Returns:
            A tuple of (result, id): the new user id on success, None on any
            failure result.
        """
        hashed_password = self._password_hasher.hash(create_user_request.password)
        user = user_converter.to_entity(create_user_request, hashed_password)
        return await self._repository.create(user)
