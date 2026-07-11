from collections.abc import AsyncGenerator, Callable
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from injector import Binder, Injector, Module

from src.api.dependencies import jwt_dependency
from src.api.routers import user
from src.application.use_cases.auth import auth_dto
from src.application.use_cases.user import user_dto as user_dto_module
from src.application.use_cases.user.create_user_use_case import CreateUserUseCase
from src.application.use_cases.user.delete_user_use_case import DeleteUserUseCase
from src.application.use_cases.user.get_all_users_use_case import GetAllUsersUseCase
from src.application.use_cases.user.get_user_use_case import GetUserUseCase
from src.application.use_cases.user.update_user_role_use_case import UpdateUserRoleUseCase
from src.domain.enums import user_enum


def _mock_current_user() -> auth_dto.TokenClaimsDTO:
    return auth_dto.TokenClaimsDTO(user_id=1, role=user_enum.UserRole.ADMIN)


@pytest.fixture
def make_user_dto() -> Callable[..., user_dto_module.UserDTO]:
    def _make_user_dto(user_id: int = 1) -> user_dto_module.UserDTO:
        return user_dto_module.UserDTO(
            id=user_id,
            email="alice@example.com",
            username="alice",
            role=user_enum.UserRole.USER,
            status=user_enum.UserStatus.ACTIVE,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )

    return _make_user_dto


@pytest.fixture
def mock_create_user_use_case() -> AsyncMock:
    return AsyncMock(spec=CreateUserUseCase)


@pytest.fixture
def mock_get_user_use_case() -> AsyncMock:
    return AsyncMock(spec=GetUserUseCase)


@pytest.fixture
def mock_get_all_users_use_case() -> AsyncMock:
    return AsyncMock(spec=GetAllUsersUseCase)


@pytest.fixture
def mock_update_user_role_use_case() -> AsyncMock:
    return AsyncMock(spec=UpdateUserRoleUseCase)


@pytest.fixture
def mock_delete_user_use_case() -> AsyncMock:
    return AsyncMock(spec=DeleteUserUseCase)


@pytest.fixture
def test_app(
    mock_create_user_use_case: AsyncMock,
    mock_get_user_use_case: AsyncMock,
    mock_get_all_users_use_case: AsyncMock,
    mock_update_user_role_use_case: AsyncMock,
    mock_delete_user_use_case: AsyncMock,
) -> FastAPI:
    # A test injector binds only what the router under test needs; the mocks
    # are instance-bound, so no request scope is required.
    class TestModule(Module):
        def configure(self, binder: Binder) -> None:
            binder.bind(CreateUserUseCase, to=mock_create_user_use_case)
            binder.bind(GetUserUseCase, to=mock_get_user_use_case)
            binder.bind(GetAllUsersUseCase, to=mock_get_all_users_use_case)
            binder.bind(UpdateUserRoleUseCase, to=mock_update_user_role_use_case)
            binder.bind(DeleteUserUseCase, to=mock_delete_user_use_case)

    app = FastAPI()
    app.include_router(user.router)
    app.state.injector = Injector([TestModule()])
    app.dependency_overrides[jwt_dependency.get_current_user] = _mock_current_user
    return app


@pytest.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as async_client:
        yield async_client
