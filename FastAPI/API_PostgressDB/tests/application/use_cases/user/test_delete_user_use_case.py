import pytest

from src.application.use_cases.user.delete_user_use_case import DeleteUserUseCase
from src.domain.enums import operation_results
from src.domain.repositories.user.user_repository import UserRepository


@pytest.fixture
def use_case(mock_repository: UserRepository) -> DeleteUserUseCase:
    return DeleteUserUseCase(repository=mock_repository)


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
