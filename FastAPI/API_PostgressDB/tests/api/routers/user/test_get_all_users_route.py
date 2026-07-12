from unittest.mock import AsyncMock

from httpx import AsyncClient


class TestGetAllUsersRoute:
    async def test_returns_200_with_list_of_users(self, client: AsyncClient, mock_get_all_users_use_case: AsyncMock, make_user_dto):
        mock_get_all_users_use_case.execute.return_value = [make_user_dto(1), make_user_dto(2)]

        response = await client.get("/api/users/v1")

        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_returns_empty_list_when_no_users_exist(self, client: AsyncClient, mock_get_all_users_use_case: AsyncMock):
        mock_get_all_users_use_case.execute.return_value = []

        response = await client.get("/api/users/v1")

        assert response.status_code == 200
        assert response.json() == []
