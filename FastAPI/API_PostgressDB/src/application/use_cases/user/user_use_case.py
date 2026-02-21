from src.application.services.password_hasher_base import PasswordHasherBase
from src.application.use_cases.user.user_converter import UserEntityConverter
from src.application.use_cases.user.user_dto import CreateUserDTO, UpdateUserRoleDTO, UserDTO
from src.application.use_cases.user.user_use_case_base import UserUseCaseBase
from src.domain.enums.operation_results import CreateResult, DeleteResult, UpdateResult
from src.domain.repositories.user.user_repository_base import UserRepositoryBase


class UserUseCase(UserUseCaseBase):
    """Use case for user operations."""

    def __init__(self, repository: UserRepositoryBase, password_hasher: PasswordHasherBase):
        """Initialize the user use case.

        Args:
            repository: The user repository for data persistence operations.
            password_hasher: The service for hashing plain-text passwords before storage.
        """
        self._repository = repository
        self._password_hasher = password_hasher

    async def create_user(self, create_user_dto: CreateUserDTO) -> tuple[CreateResult, int | None]:
        hashed_password = self._password_hasher.hash(create_user_dto.password)
        user = UserEntityConverter.to_entity(create_user_dto, hashed_password)
        return await self._repository.create(user)

    async def get_user(self, user_id: int) -> UserDTO | None:
        user = await self._repository.get_by_id(user_id)

        if user is None:
            return None

        return UserEntityConverter.to_dto(user)

    async def get_all_users(self) -> list[UserDTO]:
        users = await self._repository.get_all()
        return UserEntityConverter.to_dto_list(users)

    async def update_user_role(self, update_user_role_dto: UpdateUserRoleDTO) -> UpdateResult:
        return await self._repository.update_role(update_user_role_dto.user_id, update_user_role_dto.role)

    async def delete_user(self, user_id: int) -> DeleteResult:
        return await self._repository.delete(user_id)
