import pytest

from src.application.use_cases.user import user_dto as user_dto_module
from src.application.use_cases.user.get_all_users_use_case import GetAllUsersUseCase
from src.domain.repositories.user.user_repository import UserRepository


@pytest.fixture
def use_case(mock_repository: UserRepository) -> GetAllUsersUseCase:
    return GetAllUsersUseCase(repository=mock_repository)


class TestGetAllUsers:
    async def test_returns_dto_list_for_all_users(self, use_case, mock_repository, make_user):
        mock_repository.get_all.return_value = [make_user(1), make_user(2)]

        user_dtos = await use_case.execute()

        assert len(user_dtos) == 2
        assert all(isinstance(dto, user_dto_module.UserDTO) for dto in user_dtos)

    async def test_returns_empty_list_when_no_users_exist(self, use_case, mock_repository):
        mock_repository.get_all.return_value = []

        user_dtos = await use_case.execute()

        assert user_dtos == []

    async def test_calls_repository_get_all(self, use_case, mock_repository):
        mock_repository.get_all.return_value = []

        await use_case.execute()

        mock_repository.get_all.assert_called_once()
