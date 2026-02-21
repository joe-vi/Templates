from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.user.user_dto import CreateUserDTO, UpdateUserRoleDTO, UserDTO
from src.application.use_cases.user.user_use_case import UserUseCase
from src.domain.entities.user.user import User
from src.domain.enums.operation_results import CreateResult, DeleteResult, UpdateResult
from src.domain.enums.user_enum import UserRole, UserStatus
from src.domain.repositories.user.user_repository_base import UserRepositoryBase

def _make_user(user_id: int = 1) -> User:
    return User(
        id=user_id,
        email="alice@example.com",
        username="alice",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
    )


@pytest.fixture
def mock_repository() -> UserRepositoryBase:
    return AsyncMock(spec=UserRepositoryBase)


@pytest.fixture
def use_case(mock_repository: UserRepositoryBase) -> UserUseCase:
    return UserUseCase(repository=mock_repository)


class TestCreateUser:
    async def test_returns_success_result_and_new_id(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.create.return_value = (CreateResult.SUCCESS, 1)
        create_user_dto = CreateUserDTO(email="alice@example.com", username="alice")

        result, entity_id = await use_case.create_user(create_user_dto)

        assert result == CreateResult.SUCCESS
        assert entity_id == 1

    async def test_calls_repository_create_with_converted_entity(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.create.return_value = (CreateResult.SUCCESS, 1)
        create_user_dto = CreateUserDTO(email="alice@example.com", username="alice")

        await use_case.create_user(create_user_dto)

        mock_repository.create.assert_called_once()
        created_entity = mock_repository.create.call_args[0][0]
        assert created_entity.email == "alice@example.com"
        assert created_entity.username == "alice"
        assert created_entity.id is None

    async def test_returns_unique_constraint_error_forwarded_from_repository(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.create.return_value = (CreateResult.UNIQUE_CONSTRAINT_ERROR, None)
        create_user_dto = CreateUserDTO(email="alice@example.com", username="alice")

        result, entity_id = await use_case.create_user(create_user_dto)

        assert result == CreateResult.UNIQUE_CONSTRAINT_ERROR
        assert entity_id is None

    async def test_returns_failure_forwarded_from_repository(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.create.return_value = (CreateResult.FAILURE, None)
        create_user_dto = CreateUserDTO(email="alice@example.com", username="alice")

        result, entity_id = await use_case.create_user(create_user_dto)

        assert result == CreateResult.FAILURE
        assert entity_id is None

    async def test_returns_concurrency_error_forwarded_from_repository(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.create.return_value = (CreateResult.CONCURRENCY_ERROR, None)
        create_user_dto = CreateUserDTO(email="alice@example.com", username="alice")

        result, entity_id = await use_case.create_user(create_user_dto)

        assert result == CreateResult.CONCURRENCY_ERROR
        assert entity_id is None


class TestGetUser:
    async def test_returns_dto_when_user_found(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.get_by_id.return_value = _make_user(user_id=1)

        user_dto = await use_case.get_user(1)

        assert user_dto is not None
        assert isinstance(user_dto, UserDTO)
        assert user_dto.id == 1
        assert user_dto.email == "alice@example.com"

    async def test_returns_none_when_user_not_found(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.get_by_id.return_value = None

        user_dto = await use_case.get_user(99)

        assert user_dto is None

    async def test_calls_repository_with_correct_user_id(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.get_by_id.return_value = _make_user(user_id=5)

        await use_case.get_user(5)

        mock_repository.get_by_id.assert_called_once_with(5)

    async def test_maps_all_entity_fields_to_dto(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        created_at = datetime(2024, 1, 15, 10, 30, 0)
        mock_repository.get_by_id.return_value = User(
            id=1, email="bob@example.com", username="bob",
            role=UserRole.ADMIN, status=UserStatus.INACTIVE,
            created_at=created_at,
        )

        user_dto = await use_case.get_user(1)

        assert user_dto.role == UserRole.ADMIN
        assert user_dto.status == UserStatus.INACTIVE
        assert user_dto.created_at == created_at


class TestGetAllUsers:
    async def test_returns_dto_list_for_all_users(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.get_all.return_value = [_make_user(1), _make_user(2)]

        user_dtos = await use_case.get_all_users()

        assert len(user_dtos) == 2
        assert all(isinstance(dto, UserDTO) for dto in user_dtos)

    async def test_returns_empty_list_when_no_users_exist(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.get_all.return_value = []

        user_dtos = await use_case.get_all_users()

        assert user_dtos == []

    async def test_calls_repository_get_all(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.get_all.return_value = []

        await use_case.get_all_users()

        mock_repository.get_all.assert_called_once()


class TestUpdateUserRole:
    async def test_returns_success_result(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.update_role.return_value = UpdateResult.SUCCESS
        update_dto = UpdateUserRoleDTO(user_id=1, role=UserRole.ADMIN)

        result = await use_case.update_user_role(update_dto)

        assert result == UpdateResult.SUCCESS

    async def test_calls_repository_with_correct_user_id_and_role(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.update_role.return_value = UpdateResult.SUCCESS
        update_dto = UpdateUserRoleDTO(user_id=1, role=UserRole.ADMIN)

        await use_case.update_user_role(update_dto)

        mock_repository.update_role.assert_called_once_with(1, UserRole.ADMIN)

    async def test_returns_not_found_forwarded_from_repository(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.update_role.return_value = UpdateResult.NOT_FOUND
        update_dto = UpdateUserRoleDTO(user_id=99, role=UserRole.ADMIN)

        result = await use_case.update_user_role(update_dto)

        assert result == UpdateResult.NOT_FOUND

    async def test_returns_concurrency_error_forwarded_from_repository(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.update_role.return_value = UpdateResult.CONCURRENCY_ERROR
        update_dto = UpdateUserRoleDTO(user_id=1, role=UserRole.ADMIN)

        result = await use_case.update_user_role(update_dto)

        assert result == UpdateResult.CONCURRENCY_ERROR


class TestDeleteUser:
    async def test_returns_success_result(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.delete.return_value = DeleteResult.SUCCESS

        result = await use_case.delete_user(1)

        assert result == DeleteResult.SUCCESS

    async def test_returns_not_found_forwarded_from_repository(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.delete.return_value = DeleteResult.NOT_FOUND

        result = await use_case.delete_user(99)

        assert result == DeleteResult.NOT_FOUND

    async def test_calls_repository_with_correct_user_id(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.delete.return_value = DeleteResult.SUCCESS

        await use_case.delete_user(3)

        mock_repository.delete.assert_called_once_with(3)

    async def test_returns_concurrency_error_forwarded_from_repository(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.delete.return_value = DeleteResult.CONCURRENCY_ERROR

        result = await use_case.delete_user(1)

        assert result == DeleteResult.CONCURRENCY_ERROR
