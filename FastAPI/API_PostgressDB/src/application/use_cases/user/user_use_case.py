"""User use case implementation."""

from injector import inject

from src.application.services import password_hasher_base
from src.application.use_cases.user import (
    user_converter,
    user_dto,
    user_use_case_base,
)
from src.domain.enums import operation_results
from src.domain.repositories.user import user_repository_base


class UserUseCase(user_use_case_base.UserUseCaseBase):
    """Use case for user operations."""

    @inject
    def __init__(
        self,
        repository: user_repository_base.UserRepositoryBase,
        password_hasher: password_hasher_base.PasswordHasherBase,
    ):
        """Initialize the user use case.

        Args:
            repository: The user repository for data persistence operations.
            password_hasher: The service for hashing plain-text passwords
                before storage.
        """
        self._repository = repository
        self._password_hasher = password_hasher

    async def create_user(
        self, create_user_dto: user_dto.CreateUserDTO
    ) -> tuple[operation_results.CreateResult, int | None]:
        hashed_password = self._password_hasher.hash(create_user_dto.password)
        user = user_converter.UserEntityConverter.to_entity(
            create_user_dto, hashed_password
        )
        return await self._repository.create(user)

    async def get_user(self, user_id: int) -> user_dto.UserDTO | None:
        user = await self._repository.get_by_id(user_id)

        if user is None:
            return None

        return user_converter.UserEntityConverter.to_dto(user)

    async def get_all_users(self) -> list[user_dto.UserDTO]:
        users = await self._repository.get_all()
        return user_converter.UserEntityConverter.to_dto_list(users)

    async def update_user_role(
        self, update_user_role_dto: user_dto.UpdateUserRoleDTO
    ) -> operation_results.UpdateResult:
        return await self._repository.update_role(
            update_user_role_dto.user_id, update_user_role_dto.role
        )

    async def delete_user(self, user_id: int) -> operation_results.DeleteResult:
        return await self._repository.delete(user_id)
