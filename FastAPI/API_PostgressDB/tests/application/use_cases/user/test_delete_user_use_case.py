import pytest

from src.application.use_cases.user.delete_user_use_case import DeleteUserUseCase
from src.domain.enums import operation_results
from src.domain.repositories.user.user_repository import UserRepository
from tests.application.use_cases.user.conftest import FakeTransactionContext


@pytest.fixture
def use_case(mock_repository: UserRepository, fake_transaction_context: FakeTransactionContext) -> DeleteUserUseCase:
    return DeleteUserUseCase(repository=mock_repository, transaction_context=fake_transaction_context)


class TestDeleteUser:
    async def test_returns_success_result(self, use_case, mock_repository):
        mock_repository.delete.return_value = operation_results.DeleteResult.SUCCESS

        result = await use_case.execute(1)

        assert result == operation_results.DeleteResult.SUCCESS

    async def test_returns_not_found_forwarded_from_repository(self, use_case, mock_repository):
        mock_repository.delete.return_value = operation_results.DeleteResult.NOT_FOUND

        result = await use_case.execute(99)

        assert result == operation_results.DeleteResult.NOT_FOUND

    async def test_calls_repository_with_correct_user_id(self, use_case, mock_repository):
        mock_repository.delete.return_value = operation_results.DeleteResult.SUCCESS

        await use_case.execute(3)

        mock_repository.delete.assert_called_once_with(3)

    async def test_returns_concurrency_error_forwarded_from_repository(self, use_case, mock_repository):
        mock_repository.delete.return_value = operation_results.DeleteResult.CONCURRENCY_ERROR

        result = await use_case.execute(1)

        assert result == operation_results.DeleteResult.CONCURRENCY_ERROR


class TestDeleteUserTransactionBoundary:
    """The use case commits only on success and rolls back otherwise."""

    async def test_success_commits_transaction(self, use_case, mock_repository, fake_transaction_context):
        mock_repository.delete.return_value = operation_results.DeleteResult.SUCCESS

        await use_case.execute(1)

        assert fake_transaction_context.transaction.is_committed is True

    async def test_failure_rolls_back_without_commit(self, use_case, mock_repository, fake_transaction_context):
        mock_repository.delete.return_value = operation_results.DeleteResult.FAILURE

        await use_case.execute(1)

        assert fake_transaction_context.transaction.is_committed is False
        assert fake_transaction_context.is_rolled_back is True
