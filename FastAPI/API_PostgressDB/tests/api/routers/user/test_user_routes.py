from collections.abc import AsyncGenerator
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi_injector import attach_injector
from httpx import ASGITransport, AsyncClient
from injector import Binder, Injector, InstanceProvider, Module

from src.api.dependencies.jwt_dependency import get_current_user
from src.api.routers.user.user_routes import router
from src.application.use_cases.auth.auth_dto import TokenClaimsDTO
from src.application.use_cases.user.user_dto import UserDTO
from src.application.use_cases.user.user_use_case_base import UserUseCaseBase
from src.domain.enums.operation_results import CreateResult, DeleteResult, UpdateResult
from src.domain.enums.user_enum import UserRole, UserStatus


def _mock_current_user() -> TokenClaimsDTO:
    return TokenClaimsDTO(user_id=1, role=UserRole.ADMIN)


def _make_user_dto(user_id: int = 1) -> UserDTO:
    return UserDTO(
        id=user_id,
        email="alice@example.com",
        username="alice",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
    )


@pytest.fixture
def mock_use_case() -> AsyncMock:
    return AsyncMock(spec=UserUseCaseBase)


@pytest.fixture
def test_app(mock_use_case: AsyncMock) -> FastAPI:
    app = FastAPI()

    class TestModule(Module):
        def configure(self, binder: Binder) -> None:
            binder.bind(UserUseCaseBase, to=InstanceProvider(mock_use_case))

    test_injector = Injector([TestModule()])
    attach_injector(app, test_injector)
    app.include_router(router)
    app.dependency_overrides[get_current_user] = _mock_current_user
    return app


@pytest.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as async_client:
        yield async_client


class TestCreateUserRoute:
    async def test_returns_201_with_result_and_id_on_success(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.create_user.return_value = (CreateResult.SUCCESS, 1)

        response = await client.post("/api/v1/users", json={"email": "alice@example.com", "username": "alice", "password": "TestPass123"})

        assert response.status_code == 201
        body = response.json()
        assert body["result"] == CreateResult.SUCCESS
        assert body["id"] == 1

    async def test_returns_409_on_unique_constraint_error(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.create_user.return_value = (CreateResult.UNIQUE_CONSTRAINT_ERROR, None)

        response = await client.post("/api/v1/users", json={"email": "alice@example.com", "username": "alice", "password": "TestPass123"})

        assert response.status_code == 409
        assert response.json()["result"] == CreateResult.UNIQUE_CONSTRAINT_ERROR

    async def test_returns_409_on_concurrency_error(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.create_user.return_value = (CreateResult.CONCURRENCY_ERROR, None)

        response = await client.post("/api/v1/users", json={"email": "alice@example.com", "username": "alice", "password": "TestPass123"})

        assert response.status_code == 409
        assert response.json()["result"] == CreateResult.CONCURRENCY_ERROR

    async def test_returns_500_on_failure(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.create_user.return_value = (CreateResult.FAILURE, None)

        response = await client.post("/api/v1/users", json={"email": "alice@example.com", "username": "alice", "password": "TestPass123"})

        assert response.status_code == 500
        assert response.json()["result"] == CreateResult.FAILURE

    async def test_returns_422_on_invalid_email(self, client: AsyncClient, mock_use_case: AsyncMock):
        response = await client.post("/api/v1/users", json={"email": "not-a-valid-email", "username": "alice"})

        assert response.status_code == 422

    async def test_returns_422_when_username_is_missing(self, client: AsyncClient, mock_use_case: AsyncMock):
        response = await client.post("/api/v1/users", json={"email": "alice@example.com"})

        assert response.status_code == 422


class TestGetUserRoute:
    async def test_returns_200_with_user_data_when_found(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.get_user.return_value = _make_user_dto(user_id=1)

        response = await client.get("/api/v1/users/1")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == 1
        assert body["email"] == "alice@example.com"
        assert body["username"] == "alice"

    async def test_returns_404_when_user_not_found(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.get_user.return_value = None

        response = await client.get("/api/v1/users/99")

        assert response.status_code == 404

    async def test_calls_use_case_with_correct_user_id(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.get_user.return_value = _make_user_dto(user_id=5)

        await client.get("/api/v1/users/5")

        mock_use_case.get_user.assert_called_once_with(5)


class TestGetAllUsersRoute:
    async def test_returns_200_with_list_of_users(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.get_all_users.return_value = [_make_user_dto(1), _make_user_dto(2)]

        response = await client.get("/api/v1/users")

        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_returns_empty_list_when_no_users_exist(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.get_all_users.return_value = []

        response = await client.get("/api/v1/users")

        assert response.status_code == 200
        assert response.json() == []


class TestUpdateUserRoleRoute:
    async def test_returns_200_on_success(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.update_user_role.return_value = UpdateResult.SUCCESS

        response = await client.patch("/api/v1/users/1/role", json={"role": UserRole.ADMIN})

        assert response.status_code == 200
        assert response.json()["result"] == UpdateResult.SUCCESS

    async def test_returns_404_when_user_not_found(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.update_user_role.return_value = UpdateResult.NOT_FOUND

        response = await client.patch("/api/v1/users/99/role", json={"role": UserRole.ADMIN})

        assert response.status_code == 404

    async def test_returns_409_on_concurrency_error(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.update_user_role.return_value = UpdateResult.CONCURRENCY_ERROR

        response = await client.patch("/api/v1/users/1/role", json={"role": UserRole.ADMIN})

        assert response.status_code == 409

    async def test_returns_500_on_failure(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.update_user_role.return_value = UpdateResult.FAILURE

        response = await client.patch("/api/v1/users/1/role", json={"role": UserRole.ADMIN})

        assert response.status_code == 500

    async def test_returns_422_when_role_is_missing(self, client: AsyncClient, mock_use_case: AsyncMock):
        response = await client.patch("/api/v1/users/1/role", json={})

        assert response.status_code == 422


class TestDeleteUserRoute:
    async def test_returns_200_on_success(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.delete_user.return_value = DeleteResult.SUCCESS

        response = await client.delete("/api/v1/users/1")

        assert response.status_code == 200
        assert response.json()["result"] == DeleteResult.SUCCESS

    async def test_returns_404_when_user_not_found(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.delete_user.return_value = DeleteResult.NOT_FOUND

        response = await client.delete("/api/v1/users/99")

        assert response.status_code == 404

    async def test_returns_409_on_concurrency_error(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.delete_user.return_value = DeleteResult.CONCURRENCY_ERROR

        response = await client.delete("/api/v1/users/1")

        assert response.status_code == 409

    async def test_returns_500_on_failure(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.delete_user.return_value = DeleteResult.FAILURE

        response = await client.delete("/api/v1/users/1")

        assert response.status_code == 500

    async def test_calls_use_case_with_correct_user_id(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.delete_user.return_value = DeleteResult.SUCCESS

        await client.delete("/api/v1/users/3")

        mock_use_case.delete_user.assert_called_once_with(3)
