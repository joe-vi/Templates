from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from injector import Binder, Injector, Module

from src.api.routers.auth.router import router as auth_router
from src.application.use_cases.auth import auth_dto
from src.application.use_cases.auth.login_use_case import LoginUseCase
from src.application.use_cases.auth.refresh_token_use_case import RefreshTokenUseCase


@pytest.fixture
def make_token_dto() -> auth_dto.TokenDTO:
    return auth_dto.TokenDTO(access_token="access.jwt", refresh_token="refresh.jwt")


@pytest.fixture
def mock_login_use_case() -> AsyncMock:
    return AsyncMock(spec=LoginUseCase)


@pytest.fixture
def mock_refresh_token_use_case() -> AsyncMock:
    return AsyncMock(spec=RefreshTokenUseCase)


@pytest.fixture
def test_app(mock_login_use_case: AsyncMock, mock_refresh_token_use_case: AsyncMock) -> FastAPI:
    # A test injector binds only what the router under test needs; the mocks
    # are instance-bound, so no request scope is required.
    class TestModule(Module):
        def configure(self, binder: Binder) -> None:
            binder.bind(LoginUseCase, to=mock_login_use_case)
            binder.bind(RefreshTokenUseCase, to=mock_refresh_token_use_case)

    app = FastAPI()
    app.include_router(auth_router)
    app.state.injector = Injector([TestModule()])
    return app


@pytest.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as async_client:
        yield async_client
