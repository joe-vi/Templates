from src.application.use_cases.user.user_converter import UserEntityConverter
from src.application.use_cases.user.user_dto import CreateUserDTO, UpdateUserRoleDTO, UserDTO
from src.application.use_cases.user.user_use_case_base import UserUseCaseBase
from src.domain.enums.operation_results import CreateResult, DeleteResult, UpdateResult
from src.domain.repositories.user.user_repository_base import UserRepositoryBase


class UserUseCase(UserUseCaseBase):
    """Use case for user operations."""

    def __init__(self, repository: UserRepositoryBase):
        """Initialize the user use case.

        Args:
            repository: The user repository for data persistence operations.
        """
        self._repository = repository

    async def create_user(self, create_user_dto: CreateUserDTO) -> tuple[CreateResult, int | None]:
        user = UserEntityConverter.to_entity(create_user_dto)
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
