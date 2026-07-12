from unittest.mock import AsyncMock

from httpx import AsyncClient

from src.domain.enums import operation_results, user_enum


class TestUpdateUserRoleRoute:
    async def test_returns_200_on_success(self, client: AsyncClient, mock_update_user_role_use_case: AsyncMock):
        mock_update_user_role_use_case.execute.return_value = operation_results.UpdateResult.SUCCESS

        response = await client.patch("/api/users/v1/1/role", json={"role": user_enum.UserRole.ADMIN})

        assert response.status_code == 200
        assert response.json()["result"] == operation_results.UpdateResult.SUCCESS

    async def test_returns_404_when_user_not_found(self, client: AsyncClient, mock_update_user_role_use_case: AsyncMock):
        mock_update_user_role_use_case.execute.return_value = operation_results.UpdateResult.NOT_FOUND

        response = await client.patch("/api/users/v1/99/role", json={"role": user_enum.UserRole.ADMIN})

        assert response.status_code == 404

    async def test_returns_409_on_concurrency_error(self, client: AsyncClient, mock_update_user_role_use_case: AsyncMock):
        mock_update_user_role_use_case.execute.return_value = operation_results.UpdateResult.CONCURRENCY_ERROR

        response = await client.patch("/api/users/v1/1/role", json={"role": user_enum.UserRole.ADMIN})

        assert response.status_code == 409

    async def test_returns_500_on_failure(self, client: AsyncClient, mock_update_user_role_use_case: AsyncMock):
        mock_update_user_role_use_case.execute.return_value = operation_results.UpdateResult.FAILURE

        response = await client.patch("/api/users/v1/1/role", json={"role": user_enum.UserRole.ADMIN})

        assert response.status_code == 500

    async def test_returns_422_when_role_is_missing(self, client: AsyncClient, mock_update_user_role_use_case: AsyncMock):
        response = await client.patch("/api/users/v1/1/role", json={})

        assert response.status_code == 422
