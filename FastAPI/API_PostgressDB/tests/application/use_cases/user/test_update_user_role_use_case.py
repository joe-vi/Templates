import pytest

from src.application.use_cases.user import user_dto as user_dto_module
from src.application.use_cases.user.update_user_role_use_case import UpdateUserRoleUseCase
from src.domain.enums import operation_results, user_enum
from src.domain.repositories.user.user_repository import UserRepository
from tests.application.use_cases.user.conftest import FakeTransactionContext


@pytest.fixture
def use_case(mock_repository: UserRepository, fake_transaction_context: FakeTransactionContext) -> UpdateUserRoleUseCase:
    return UpdateUserRoleUseCase(repository=mock_repository, transaction_context=fake_transaction_context)


class TestUpdateUserRole:
    async def test_returns_success_result(self, use_case, mock_repository):
        mock_repository.update_role.return_value = operation_results.UpdateResult.SUCCESS
        update_dto = user_dto_module.UpdateUserRoleDTO(user_id=1, role=user_enum.UserRole.ADMIN)

        result = await use_case.execute(update_dto)

        assert result == operation_results.UpdateResult.SUCCESS

    async def test_calls_repository_with_correct_user_id_and_role(self, use_case, mock_repository):
        mock_repository.update_role.return_value = operation_results.UpdateResult.SUCCESS
        update_dto = user_dto_module.UpdateUserRoleDTO(user_id=1, role=user_enum.UserRole.ADMIN)

        await use_case.execute(update_dto)

        mock_repository.update_role.assert_called_once_with(1, user_enum.UserRole.ADMIN)

    async def test_returns_not_found_forwarded_from_repository(self, use_case, mock_repository):
        mock_repository.update_role.return_value = operation_results.UpdateResult.NOT_FOUND
        update_dto = user_dto_module.UpdateUserRoleDTO(user_id=99, role=user_enum.UserRole.ADMIN)

        result = await use_case.execute(update_dto)

        assert result == operation_results.UpdateResult.NOT_FOUND

    async def test_returns_concurrency_error_forwarded_from_repository(self, use_case, mock_repository):
        mock_repository.update_role.return_value = operation_results.UpdateResult.CONCURRENCY_ERROR
        update_dto = user_dto_module.UpdateUserRoleDTO(user_id=1, role=user_enum.UserRole.ADMIN)

        result = await use_case.execute(update_dto)

        assert result == operation_results.UpdateResult.CONCURRENCY_ERROR


class TestUpdateUserRoleTransactionBoundary:
    """The use case commits only on success and rolls back otherwise."""

    async def test_success_commits_transaction(self, use_case, mock_repository, fake_transaction_context):
        mock_repository.update_role.return_value = operation_results.UpdateResult.SUCCESS

        await use_case.execute(user_dto_module.UpdateUserRoleDTO(user_id=1, role=user_enum.UserRole.ADMIN))

        assert fake_transaction_context.transaction.is_committed is True

    async def test_not_found_rolls_back_without_commit(self, use_case, mock_repository, fake_transaction_context):
        mock_repository.update_role.return_value = operation_results.UpdateResult.NOT_FOUND

        await use_case.execute(user_dto_module.UpdateUserRoleDTO(user_id=99, role=user_enum.UserRole.ADMIN))

        assert fake_transaction_context.transaction.is_committed is False
        assert fake_transaction_context.is_rolled_back is True
