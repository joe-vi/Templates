from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from injector import Binder, Injector, Module

from src.api.routers.auth import auth_routes
from src.application.use_cases.auth import auth_dto
from src.application.use_cases.auth.auth_use_case import AuthUseCase
from src.domain.enums import operation_results


def _make_token_dto() -> auth_dto.TokenDTO:
    return auth_dto.TokenDTO(access_token="access.jwt", refresh_token="refresh.jwt")


@pytest.fixture
def mock_use_case() -> AsyncMock:
    return AsyncMock(spec=AuthUseCase)


@pytest.fixture
def test_app(mock_use_case: AsyncMock) -> FastAPI:
    # A test injector binds only what the router under test needs; the mock
    # is instance-bound, so no request scope is required.
    class TestModule(Module):
        def configure(self, binder: Binder) -> None:
            binder.bind(AuthUseCase, to=mock_use_case)

    app = FastAPI()
    app.include_router(auth_routes.router)
    app.state.injector = Injector([TestModule()])
    return app


@pytest.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as async_client:
        yield async_client


class TestLoginRoute:
    async def test_returns_200_with_camel_case_token_pair_on_success(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.login.return_value = (operation_results.LoginResult.SUCCESS, _make_token_dto())

        response = await client.post("/api/v1/auth/login", json={"username": "alice", "password": "TestPass123"})

        assert response.status_code == 200
        body = response.json()
        assert body["accessToken"] == "access.jwt"
        assert body["refreshToken"] == "refresh.jwt"
        assert body["tokenType"] == "bearer"

    async def test_returns_401_on_invalid_credentials(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.login.return_value = (operation_results.LoginResult.INVALID_CREDENTIALS, None)

        response = await client.post("/api/v1/auth/login", json={"username": "alice", "password": "wrong"})

        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Bearer"

    async def test_returns_403_when_account_is_inactive(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.login.return_value = (operation_results.LoginResult.USER_INACTIVE, None)

        response = await client.post("/api/v1/auth/login", json={"username": "alice", "password": "TestPass123"})

        assert response.status_code == 403

    async def test_returns_500_on_unexpected_failure(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.login.return_value = (operation_results.LoginResult.FAILURE, None)

        response = await client.post("/api/v1/auth/login", json={"username": "alice", "password": "TestPass123"})

        assert response.status_code == 500

    async def test_returns_422_when_fields_are_missing(self, client: AsyncClient, mock_use_case: AsyncMock):
        response = await client.post("/api/v1/auth/login", json={})

        assert response.status_code == 422

    async def test_passes_credentials_to_use_case(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.login.return_value = (operation_results.LoginResult.SUCCESS, _make_token_dto())

        await client.post("/api/v1/auth/login", json={"username": "alice", "password": "TestPass123"})

        mock_use_case.login.assert_called_once()
        login_dto = mock_use_case.login.call_args[0][0]
        assert login_dto.username == "alice"
        assert login_dto.password == "TestPass123"


class TestRefreshTokenRoute:
    async def test_returns_200_with_new_token_pair_on_success(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.refresh_token.return_value = (operation_results.LoginResult.SUCCESS, _make_token_dto())

        response = await client.post("/api/v1/auth/refresh", json={"refreshToken": "refresh.jwt"})

        assert response.status_code == 200
        assert response.json()["accessToken"] == "access.jwt"

    async def test_accepts_snake_case_body_field(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.refresh_token.return_value = (operation_results.LoginResult.SUCCESS, _make_token_dto())

        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": "refresh.jwt"})

        assert response.status_code == 200

    async def test_returns_401_on_invalid_refresh_token(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.refresh_token.return_value = (operation_results.LoginResult.INVALID_CREDENTIALS, None)

        response = await client.post("/api/v1/auth/refresh", json={"refreshToken": "garbage"})

        assert response.status_code == 401

    async def test_returns_422_when_refresh_token_is_missing(self, client: AsyncClient, mock_use_case: AsyncMock):
        response = await client.post("/api/v1/auth/refresh", json={})

        assert response.status_code == 422
