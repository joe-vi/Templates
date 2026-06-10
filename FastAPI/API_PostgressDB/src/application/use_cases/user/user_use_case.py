"""User use case."""

from src.application.services.password_hasher import PasswordHasher
from src.application.use_cases.user import user_converter, user_dto
from src.domain.enums import operation_results
from src.domain.repositories.user.user_repository import UserRepository


class UserUseCase:
    """Application logic for user operations.

    Depends only on ports (``UserRepository``, ``PasswordHasher``); the
    concrete adapters are supplied by the API dependency providers.
    """

    def __init__(
        self,
        repository: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        """Initialize the user use case.

        Args:
            repository: The user repository port for persistence.
            password_hasher: The port for hashing plain-text passwords.
        """
        self._repository = repository
        self._password_hasher = password_hasher

    async def create_user(
        self, create_user_dto: user_dto.CreateUserDTO
    ) -> tuple[operation_results.CreateResult, int | None]:
        """Create a new user. See create flow in the repository port."""
        hashed_password = self._password_hasher.hash(create_user_dto.password)
        user = user_converter.to_entity(create_user_dto, hashed_password)
        return await self._repository.create(user)

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
        return await self._repository.update_role(
            update_user_role_dto.user_id, update_user_role_dto.role
        )

    async def delete_user(self, user_id: int) -> operation_results.DeleteResult:
        """Delete the user with the given id."""
        return await self._repository.delete(user_id)
