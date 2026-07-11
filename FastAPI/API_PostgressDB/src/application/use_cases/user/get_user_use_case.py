from injector import inject

from src.application.use_cases.user import user_converter, user_dto
from src.domain.repositories.user.user_repository import UserRepository


class GetUserUseCase:
    """Application logic for reading a single user.

    One use case class per operation: a pure read, so it depends only on the
    repository port — no password hasher, no transaction context.
    """

    @inject
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self, user_id: int) -> user_dto.UserDTO | None:
        """Return the user with the given id.

        Args:
            user_id: The unique identifier of the user.

        Returns:
            The UserDTO if found, None otherwise.
        """
        user = await self._repository.get_by_id(user_id)

        if user is None:
            return None

        return user_converter.to_dto(user)
