from unittest.mock import AsyncMock

from httpx import AsyncClient

from src.domain.enums import operation_results


class TestCreateUserRoute:
    async def test_returns_201_with_result_and_id_on_success(self, client: AsyncClient, mock_create_user_use_case: AsyncMock):
        mock_create_user_use_case.execute.return_value = (operation_results.CreateResult.SUCCESS, 1)

        response = await client.post("/api/users/v1", json={"email": "alice@example.com", "username": "alice", "password": "TestPass123"})

        assert response.status_code == 201
        body = response.json()
        assert body["result"] == operation_results.CreateResult.SUCCESS
        assert body["id"] == 1

    async def test_returns_409_on_unique_constraint_error(self, client: AsyncClient, mock_create_user_use_case: AsyncMock):
        mock_create_user_use_case.execute.return_value = (operation_results.CreateResult.UNIQUE_CONSTRAINT_ERROR, None)

        response = await client.post("/api/users/v1", json={"email": "alice@example.com", "username": "alice", "password": "TestPass123"})

        assert response.status_code == 409
        assert response.json()["result"] == operation_results.CreateResult.UNIQUE_CONSTRAINT_ERROR

    async def test_returns_409_on_concurrency_error(self, client: AsyncClient, mock_create_user_use_case: AsyncMock):
        mock_create_user_use_case.execute.return_value = (operation_results.CreateResult.CONCURRENCY_ERROR, None)

        response = await client.post("/api/users/v1", json={"email": "alice@example.com", "username": "alice", "password": "TestPass123"})

        assert response.status_code == 409
        assert response.json()["result"] == operation_results.CreateResult.CONCURRENCY_ERROR

    async def test_returns_500_on_failure(self, client: AsyncClient, mock_create_user_use_case: AsyncMock):
        mock_create_user_use_case.execute.return_value = (operation_results.CreateResult.FAILURE, None)

        response = await client.post("/api/users/v1", json={"email": "alice@example.com", "username": "alice", "password": "TestPass123"})

        assert response.status_code == 500
        assert response.json()["result"] == operation_results.CreateResult.FAILURE

    async def test_returns_422_on_invalid_email(self, client: AsyncClient, mock_create_user_use_case: AsyncMock):
        response = await client.post("/api/users/v1", json={"email": "not-a-valid-email", "username": "alice"})

        assert response.status_code == 422

    async def test_returns_422_when_username_is_missing(self, client: AsyncClient, mock_create_user_use_case: AsyncMock):
        response = await client.post("/api/users/v1", json={"email": "alice@example.com"})

        assert response.status_code == 422
