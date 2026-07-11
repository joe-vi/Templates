from injector import inject

from src.application.use_cases.user import user_converter, user_dto
from src.domain.repositories.user.user_repository import UserRepository


class GetAllUsersUseCase:
    """Application logic for listing all users.

    One use case class per operation: a pure read, so it depends only on the
    repository port.
    """

    @inject
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self) -> list[user_dto.UserDTO]:
        """Return all users.

        Returns:
            All users as DTOs; an empty list when there are none.
        """
        users = await self._repository.get_all()
        return user_converter.to_dto_list(users)
