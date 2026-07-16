from injector import inject

from src.application.use_cases.user import user_contracts, user_converter
from src.domain.repositories.user.user_repository import UserRepository


class GetAllUsersUseCase:
    """Retrieves all users."""

    @inject
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self) -> list[user_contracts.UserResponse]:
        """Return all users.

        Returns:
            All users as response models; an empty list when there are none.
        """
        users = await self._repository.get_all()
        return user_converter.to_response_list(users)
