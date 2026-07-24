import pytest

from src.application.use_cases.user import user_contracts
from src.application.use_cases.user.create_user_use_case import CreateUserUseCase
from src.domain.enums import operation_results
from src.domain.repositories.user.user_repository import UserRepository
from src.ports.password_hasher import PasswordHasher


@pytest.fixture
def use_case(mock_repository: UserRepository, mock_password_hasher: PasswordHasher) -> CreateUserUseCase:
    return CreateUserUseCase(repository=mock_repository, password_hasher=mock_password_hasher)


def _make_create_user_request() -> user_contracts.CreateUserRequest:
    return user_contracts.CreateUserRequest(email="alice@example.com", username="alice", password="TestPass123")


class TestCreateUser:
    async def test_returns_success_result_and_new_id(self, use_case, mock_repository):
        mock_repository.create.return_value = (operation_results.CreateResult.SUCCESS, 1)

        result, entity_id = await use_case.execute(_make_create_user_request())

        assert result == operation_results.CreateResult.SUCCESS
        assert entity_id == 1

    async def test_calls_repository_create_with_converted_entity(self, use_case, mock_repository):
        mock_repository.create.return_value = (operation_results.CreateResult.SUCCESS, 1)

        await use_case.execute(_make_create_user_request())

        mock_repository.create.assert_called_once()
        created_entity = mock_repository.create.call_args[0][0]
        assert created_entity.email == "alice@example.com"
        assert created_entity.username == "alice"
        assert created_entity.id is None

    async def test_returns_unique_constraint_error_forwarded_from_repository(self, use_case, mock_repository):
        mock_repository.create.return_value = (operation_results.CreateResult.UNIQUE_CONSTRAINT_ERROR, None)

        result, entity_id = await use_case.execute(_make_create_user_request())

        assert result == operation_results.CreateResult.UNIQUE_CONSTRAINT_ERROR
        assert entity_id is None

    async def test_returns_failure_forwarded_from_repository(self, use_case, mock_repository):
        mock_repository.create.return_value = (operation_results.CreateResult.FAILURE, None)

        result, entity_id = await use_case.execute(_make_create_user_request())

        assert result == operation_results.CreateResult.FAILURE
        assert entity_id is None

    async def test_returns_concurrency_error_forwarded_from_repository(self, use_case, mock_repository):
        mock_repository.create.return_value = (operation_results.CreateResult.CONCURRENCY_ERROR, None)

        result, entity_id = await use_case.execute(_make_create_user_request())

        assert result == operation_results.CreateResult.CONCURRENCY_ERROR
        assert entity_id is None
