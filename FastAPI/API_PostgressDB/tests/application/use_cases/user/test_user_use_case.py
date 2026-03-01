"""Unit tests for UserUseCase."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.services import password_hasher_base
from src.application.use_cases.user import user_dto as user_dto_module
from src.application.use_cases.user import user_use_case
from src.domain.entities.user import user as user_module
from src.domain.enums import operation_results, user_enum
from src.domain.repositories.user import user_repository_base


def _make_user(user_id: int = 1) -> user_module.User:
    return user_module.User(
        id=user_id,
        email="alice@example.com",
        username="alice",
        role=user_enum.UserRole.USER,
        status=user_enum.UserStatus.ACTIVE,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
    )


@pytest.fixture
def mock_repository() -> user_repository_base.UserRepositoryBase:
    return AsyncMock(spec=user_repository_base.UserRepositoryBase)


@pytest.fixture
def mock_password_hasher() -> password_hasher_base.PasswordHasherBase:
    hasher = MagicMock(spec=password_hasher_base.PasswordHasherBase)
    hasher.hash.return_value = "hashed_password"
    return hasher


@pytest.fixture
def use_case(
    mock_repository: user_repository_base.UserRepositoryBase,
    mock_password_hasher: password_hasher_base.PasswordHasherBase,
) -> user_use_case.UserUseCase:
    return user_use_case.UserUseCase(
        repository=mock_repository, password_hasher=mock_password_hasher
    )


class TestCreateUser:
    async def test_returns_success_result_and_new_id(
        self, use_case, mock_repository
    ):
        mock_repository.create.return_value = (
            operation_results.CreateResult.SUCCESS,
            1,
        )
        create_user_dto = user_dto_module.CreateUserDTO(
            email="alice@example.com", username="alice", password="TestPass123"
        )

        result, entity_id = await use_case.create_user(create_user_dto)

        assert result == operation_results.CreateResult.SUCCESS
        assert entity_id == 1

    async def test_calls_repository_create_with_converted_entity(
        self, use_case, mock_repository
    ):
        mock_repository.create.return_value = (
            operation_results.CreateResult.SUCCESS,
            1,
        )
        create_user_dto = user_dto_module.CreateUserDTO(
            email="alice@example.com", username="alice", password="TestPass123"
        )

        await use_case.create_user(create_user_dto)

        mock_repository.create.assert_called_once()
        created_entity = mock_repository.create.call_args[0][0]
        assert created_entity.email == "alice@example.com"
        assert created_entity.username == "alice"
        assert created_entity.id is None

    async def test_returns_unique_constraint_error_forwarded_from_repository(
        self, use_case, mock_repository
    ):
        mock_repository.create.return_value = (
            operation_results.CreateResult.UNIQUE_CONSTRAINT_ERROR,
            None,
        )
        create_user_dto = user_dto_module.CreateUserDTO(
            email="alice@example.com", username="alice", password="TestPass123"
        )

        result, entity_id = await use_case.create_user(create_user_dto)

        assert result == operation_results.CreateResult.UNIQUE_CONSTRAINT_ERROR
        assert entity_id is None

    async def test_returns_failure_forwarded_from_repository(
        self, use_case, mock_repository
    ):
        mock_repository.create.return_value = (
            operation_results.CreateResult.FAILURE,
            None,
        )
        create_user_dto = user_dto_module.CreateUserDTO(
            email="alice@example.com", username="alice", password="TestPass123"
        )

        result, entity_id = await use_case.create_user(create_user_dto)

        assert result == operation_results.CreateResult.FAILURE
        assert entity_id is None

    async def test_returns_concurrency_error_forwarded_from_repository(
        self, use_case, mock_repository
    ):
        mock_repository.create.return_value = (
            operation_results.CreateResult.CONCURRENCY_ERROR,
            None,
        )
        create_user_dto = user_dto_module.CreateUserDTO(
            email="alice@example.com", username="alice", password="TestPass123"
        )

        result, entity_id = await use_case.create_user(create_user_dto)

        assert result == operation_results.CreateResult.CONCURRENCY_ERROR
        assert entity_id is None


class TestGetUser:
    async def test_returns_dto_when_user_found(self, use_case, mock_repository):
        mock_repository.get_by_id.return_value = _make_user(user_id=1)

        result_dto = await use_case.get_user(1)

        assert result_dto is not None
        assert isinstance(result_dto, user_dto_module.UserDTO)
        assert result_dto.id == 1
        assert result_dto.email == "alice@example.com"

    async def test_returns_none_when_user_not_found(
        self, use_case, mock_repository
    ):
        mock_repository.get_by_id.return_value = None

        result_dto = await use_case.get_user(99)

        assert result_dto is None

    async def test_calls_repository_with_correct_user_id(
        self, use_case, mock_repository
    ):
        mock_repository.get_by_id.return_value = _make_user(user_id=5)

        await use_case.get_user(5)

        mock_repository.get_by_id.assert_called_once_with(5)

    async def test_maps_all_entity_fields_to_dto(
        self, use_case, mock_repository
    ):
        created_at = datetime(2024, 1, 15, 10, 30, 0)
        mock_repository.get_by_id.return_value = user_module.User(
            id=1,
            email="bob@example.com",
            username="bob",
            role=user_enum.UserRole.ADMIN,
            status=user_enum.UserStatus.INACTIVE,
            created_at=created_at,
        )

        result_dto = await use_case.get_user(1)

        assert result_dto.role == user_enum.UserRole.ADMIN
        assert result_dto.status == user_enum.UserStatus.INACTIVE
        assert result_dto.created_at == created_at


class TestGetAllUsers:
    async def test_returns_dto_list_for_all_users(
        self, use_case, mock_repository
    ):
        mock_repository.get_all.return_value = [_make_user(1), _make_user(2)]

        user_dtos = await use_case.get_all_users()

        assert len(user_dtos) == 2
        assert all(
            isinstance(dto, user_dto_module.UserDTO) for dto in user_dtos
        )

    async def test_returns_empty_list_when_no_users_exist(
        self, use_case, mock_repository
    ):
        mock_repository.get_all.return_value = []

        user_dtos = await use_case.get_all_users()

        assert user_dtos == []

    async def test_calls_repository_get_all(self, use_case, mock_repository):
        mock_repository.get_all.return_value = []

        await use_case.get_all_users()

        mock_repository.get_all.assert_called_once()


class TestUpdateUserRole:
    async def test_returns_success_result(self, use_case, mock_repository):
        mock_repository.update_role.return_value = (
            operation_results.UpdateResult.SUCCESS
        )
        update_dto = user_dto_module.UpdateUserRoleDTO(
            user_id=1, role=user_enum.UserRole.ADMIN
        )

        result = await use_case.update_user_role(update_dto)

        assert result == operation_results.UpdateResult.SUCCESS

    async def test_calls_repository_with_correct_user_id_and_role(
        self, use_case, mock_repository
    ):
        mock_repository.update_role.return_value = (
            operation_results.UpdateResult.SUCCESS
        )
        update_dto = user_dto_module.UpdateUserRoleDTO(
            user_id=1, role=user_enum.UserRole.ADMIN
        )

        await use_case.update_user_role(update_dto)

        mock_repository.update_role.assert_called_once_with(
            1, user_enum.UserRole.ADMIN
        )

    async def test_returns_not_found_forwarded_from_repository(
        self, use_case, mock_repository
    ):
        mock_repository.update_role.return_value = (
            operation_results.UpdateResult.NOT_FOUND
        )
        update_dto = user_dto_module.UpdateUserRoleDTO(
            user_id=99, role=user_enum.UserRole.ADMIN
        )

        result = await use_case.update_user_role(update_dto)

        assert result == operation_results.UpdateResult.NOT_FOUND

    async def test_returns_concurrency_error_forwarded_from_repository(
        self, use_case, mock_repository
    ):
        mock_repository.update_role.return_value = (
            operation_results.UpdateResult.CONCURRENCY_ERROR
        )
        update_dto = user_dto_module.UpdateUserRoleDTO(
            user_id=1, role=user_enum.UserRole.ADMIN
        )

        result = await use_case.update_user_role(update_dto)

        assert result == operation_results.UpdateResult.CONCURRENCY_ERROR


class TestDeleteUser:
    async def test_returns_success_result(self, use_case, mock_repository):
        mock_repository.delete.return_value = (
            operation_results.DeleteResult.SUCCESS
        )

        result = await use_case.delete_user(1)

        assert result == operation_results.DeleteResult.SUCCESS

    async def test_returns_not_found_forwarded_from_repository(
        self, use_case, mock_repository
    ):
        mock_repository.delete.return_value = (
            operation_results.DeleteResult.NOT_FOUND
        )

        result = await use_case.delete_user(99)

        assert result == operation_results.DeleteResult.NOT_FOUND

    async def test_calls_repository_with_correct_user_id(
        self, use_case, mock_repository
    ):
        mock_repository.delete.return_value = (
            operation_results.DeleteResult.SUCCESS
        )

        await use_case.delete_user(3)

        mock_repository.delete.assert_called_once_with(3)

    async def test_returns_concurrency_error_forwarded_from_repository(
        self, use_case, mock_repository
    ):
        mock_repository.delete.return_value = (
            operation_results.DeleteResult.CONCURRENCY_ERROR
        )

        result = await use_case.delete_user(1)

        assert result == operation_results.DeleteResult.CONCURRENCY_ERROR
