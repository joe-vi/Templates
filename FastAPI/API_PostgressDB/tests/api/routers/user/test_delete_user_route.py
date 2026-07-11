from unittest.mock import AsyncMock

from httpx import AsyncClient

from src.domain.enums import operation_results


class TestDeleteUserRoute:
    async def test_returns_200_on_success(self, client: AsyncClient, mock_delete_user_use_case: AsyncMock):
        mock_delete_user_use_case.execute.return_value = operation_results.DeleteResult.SUCCESS

        response = await client.delete("/api/v1/users/1")

        assert response.status_code == 200
        assert response.json()["result"] == operation_results.DeleteResult.SUCCESS

    async def test_returns_404_when_user_not_found(self, client: AsyncClient, mock_delete_user_use_case: AsyncMock):
        mock_delete_user_use_case.execute.return_value = operation_results.DeleteResult.NOT_FOUND

        response = await client.delete("/api/v1/users/99")

        assert response.status_code == 404

    async def test_returns_409_on_concurrency_error(self, client: AsyncClient, mock_delete_user_use_case: AsyncMock):
        mock_delete_user_use_case.execute.return_value = operation_results.DeleteResult.CONCURRENCY_ERROR

        response = await client.delete("/api/v1/users/1")

        assert response.status_code == 409

    async def test_returns_500_on_failure(self, client: AsyncClient, mock_delete_user_use_case: AsyncMock):
        mock_delete_user_use_case.execute.return_value = operation_results.DeleteResult.FAILURE

        response = await client.delete("/api/v1/users/1")

        assert response.status_code == 500

    async def test_calls_use_case_with_correct_user_id(self, client: AsyncClient, mock_delete_user_use_case: AsyncMock):
        mock_delete_user_use_case.execute.return_value = operation_results.DeleteResult.SUCCESS

        await client.delete("/api/v1/users/3")

        mock_delete_user_use_case.execute.assert_called_once_with(3)
