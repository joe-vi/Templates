import pytest

from src.application.use_cases.user.update_user_role_use_case import UpdateUserRoleUseCase
from src.domain.enums import operation_results, user_enum
from src.domain.repositories.user.user_repository import UserRepository


@pytest.fixture
def use_case(mock_repository: UserRepository) -> UpdateUserRoleUseCase:
    return UpdateUserRoleUseCase(repository=mock_repository)


class TestUpdateUserRole:
    async def test_returns_success_result(self, use_case, mock_repository):
        mock_repository.update_role.return_value = operation_results.UpdateResult.SUCCESS

        result = await use_case.execute(1, user_enum.UserRole.ADMIN)

        assert result == operation_results.UpdateResult.SUCCESS

    async def test_calls_repository_with_correct_user_id_and_role(self, use_case, mock_repository):
        mock_repository.update_role.return_value = operation_results.UpdateResult.SUCCESS

        await use_case.execute(1, user_enum.UserRole.ADMIN)

        mock_repository.update_role.assert_called_once_with(1, user_enum.UserRole.ADMIN)

    async def test_returns_not_found_forwarded_from_repository(self, use_case, mock_repository):
        mock_repository.update_role.return_value = operation_results.UpdateResult.NOT_FOUND

        result = await use_case.execute(99, user_enum.UserRole.ADMIN)

        assert result == operation_results.UpdateResult.NOT_FOUND

    async def test_returns_concurrency_error_forwarded_from_repository(self, use_case, mock_repository):
        mock_repository.update_role.return_value = operation_results.UpdateResult.CONCURRENCY_ERROR

        result = await use_case.execute(1, user_enum.UserRole.ADMIN)

        assert result == operation_results.UpdateResult.CONCURRENCY_ERROR
