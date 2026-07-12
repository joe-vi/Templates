from datetime import datetime

import pytest

from src.application.use_cases.user import user_dto as user_dto_module
from src.application.use_cases.user.get_user_use_case import GetUserUseCase
from src.domain.entities.user import user as user_module
from src.domain.enums import user_enum
from src.domain.repositories.user.user_repository import UserRepository


@pytest.fixture
def use_case(mock_repository: UserRepository) -> GetUserUseCase:
    return GetUserUseCase(repository=mock_repository)


class TestGetUser:
    async def test_returns_dto_when_user_found(self, use_case, mock_repository, make_user):
        mock_repository.get_by_id.return_value = make_user(user_id=1)

        result_dto = await use_case.execute(1)

        assert result_dto is not None
        assert isinstance(result_dto, user_dto_module.UserDTO)
        assert result_dto.id == 1
        assert result_dto.email == "alice@example.com"

    async def test_returns_none_when_user_not_found(self, use_case, mock_repository):
        mock_repository.get_by_id.return_value = None

        result_dto = await use_case.execute(99)

        assert result_dto is None

    async def test_calls_repository_with_correct_user_id(self, use_case, mock_repository, make_user):
        mock_repository.get_by_id.return_value = make_user(user_id=5)

        await use_case.execute(5)

        mock_repository.get_by_id.assert_called_once_with(5)

    async def test_maps_all_entity_fields_to_dto(self, use_case, mock_repository):
        created_at = datetime(2024, 1, 15, 10, 30, 0)
        mock_repository.get_by_id.return_value = user_module.User(
            id=1,
            email="bob@example.com",
            username="bob",
            role=user_enum.UserRole.ADMIN,
            status=user_enum.UserStatus.INACTIVE,
            created_at=created_at,
        )

        result_dto = await use_case.execute(1)

        assert result_dto.role == user_enum.UserRole.ADMIN
        assert result_dto.status == user_enum.UserStatus.INACTIVE
        assert result_dto.created_at == created_at
