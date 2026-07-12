from unittest.mock import AsyncMock

from httpx import AsyncClient

from src.application.use_cases.auth import auth_dto
from src.domain.enums import operation_results


class TestRefreshTokenRoute:
    async def test_returns_200_with_new_token_pair_on_success(
        self, client: AsyncClient, mock_refresh_token_use_case: AsyncMock, make_token_dto: auth_dto.TokenDTO
    ):
        mock_refresh_token_use_case.execute.return_value = (operation_results.LoginResult.SUCCESS, make_token_dto)

        response = await client.post("/api/auth/v1/refresh", json={"refreshToken": "refresh.jwt"})

        assert response.status_code == 200
        assert response.json()["accessToken"] == "access.jwt"

    async def test_accepts_snake_case_body_field(
        self, client: AsyncClient, mock_refresh_token_use_case: AsyncMock, make_token_dto: auth_dto.TokenDTO
    ):
        mock_refresh_token_use_case.execute.return_value = (operation_results.LoginResult.SUCCESS, make_token_dto)

        response = await client.post("/api/auth/v1/refresh", json={"refresh_token": "refresh.jwt"})

        assert response.status_code == 200

    async def test_returns_401_on_invalid_refresh_token(self, client: AsyncClient, mock_refresh_token_use_case: AsyncMock):
        mock_refresh_token_use_case.execute.return_value = (operation_results.LoginResult.INVALID_CREDENTIALS, None)

        response = await client.post("/api/auth/v1/refresh", json={"refreshToken": "garbage"})

        assert response.status_code == 401

    async def test_returns_422_when_refresh_token_is_missing(self, client: AsyncClient, mock_refresh_token_use_case: AsyncMock):
        response = await client.post("/api/auth/v1/refresh", json={})

        assert response.status_code == 422
