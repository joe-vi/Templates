from unittest.mock import AsyncMock

from httpx import AsyncClient

from src.application.use_cases.auth import auth_dto
from src.domain.enums import operation_results


class TestLoginRoute:
    async def test_returns_200_with_camel_case_token_pair_on_success(
        self, client: AsyncClient, mock_login_use_case: AsyncMock, make_token_dto: auth_dto.TokenDTO
    ):
        mock_login_use_case.execute.return_value = (operation_results.LoginResult.SUCCESS, make_token_dto)

        response = await client.post("/api/auth/v1/login", json={"username": "alice", "password": "TestPass123"})

        assert response.status_code == 200
        body = response.json()
        assert body["accessToken"] == "access.jwt"
        assert body["refreshToken"] == "refresh.jwt"
        assert body["tokenType"] == "bearer"

    async def test_returns_401_on_invalid_credentials(self, client: AsyncClient, mock_login_use_case: AsyncMock):
        mock_login_use_case.execute.return_value = (operation_results.LoginResult.INVALID_CREDENTIALS, None)

        response = await client.post("/api/auth/v1/login", json={"username": "alice", "password": "wrong"})

        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Bearer"

    async def test_returns_403_when_account_is_inactive(self, client: AsyncClient, mock_login_use_case: AsyncMock):
        mock_login_use_case.execute.return_value = (operation_results.LoginResult.USER_INACTIVE, None)

        response = await client.post("/api/auth/v1/login", json={"username": "alice", "password": "TestPass123"})

        assert response.status_code == 403

    async def test_returns_500_on_unexpected_failure(self, client: AsyncClient, mock_login_use_case: AsyncMock):
        mock_login_use_case.execute.return_value = (operation_results.LoginResult.FAILURE, None)

        response = await client.post("/api/auth/v1/login", json={"username": "alice", "password": "TestPass123"})

        assert response.status_code == 500

    async def test_returns_422_when_fields_are_missing(self, client: AsyncClient, mock_login_use_case: AsyncMock):
        response = await client.post("/api/auth/v1/login", json={})

        assert response.status_code == 422

    async def test_passes_credentials_to_use_case(
        self, client: AsyncClient, mock_login_use_case: AsyncMock, make_token_dto: auth_dto.TokenDTO
    ):
        mock_login_use_case.execute.return_value = (operation_results.LoginResult.SUCCESS, make_token_dto)

        await client.post("/api/auth/v1/login", json={"username": "alice", "password": "TestPass123"})

        mock_login_use_case.execute.assert_called_once()
        login_dto = mock_login_use_case.execute.call_args[0][0]
        assert login_dto.username == "alice"
        assert login_dto.password == "TestPass123"
