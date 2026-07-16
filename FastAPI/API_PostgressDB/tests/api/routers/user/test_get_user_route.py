from unittest.mock import AsyncMock

from httpx import AsyncClient


class TestGetUserRoute:
    async def test_returns_200_with_user_data_when_found(self, client: AsyncClient, mock_get_user_use_case: AsyncMock, make_user_response):
        mock_get_user_use_case.execute.return_value = make_user_response(user_id=1)

        response = await client.get("/api/users/v1/1")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == 1
        assert body["email"] == "alice@example.com"
        assert body["username"] == "alice"

    async def test_returns_404_when_user_not_found(self, client: AsyncClient, mock_get_user_use_case: AsyncMock):
        mock_get_user_use_case.execute.return_value = None

        response = await client.get("/api/users/v1/99")

        assert response.status_code == 404

    async def test_calls_use_case_with_correct_user_id(self, client: AsyncClient, mock_get_user_use_case: AsyncMock, make_user_response):
        mock_get_user_use_case.execute.return_value = make_user_response(user_id=5)

        await client.get("/api/users/v1/5")

        mock_get_user_use_case.execute.assert_called_once_with(5)
