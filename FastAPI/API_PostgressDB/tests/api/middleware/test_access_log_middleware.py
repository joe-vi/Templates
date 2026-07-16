from collections.abc import AsyncGenerator
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from injector import Binder, Injector, InstanceProvider, Module

from src.api.middleware import registration
from src.ports.logger import Logger


@pytest.fixture
def mock_logger() -> Mock:
    return Mock(spec=Logger)


@pytest.fixture
def test_app(mock_logger: Mock) -> FastAPI:
    # InstanceProvider bypasses injector's isinstance check, which a non-runtime_checkable
    # Protocol port cannot satisfy.
    class TestModule(Module):
        def configure(self, binder: Binder) -> None:
            binder.bind(Logger, to=InstanceProvider(mock_logger))

    app = FastAPI()

    @app.get("/probe")
    async def probe() -> dict[str, str]:
        return {"status": "ok"}

    registration.register(app)
    app.state.injector = Injector([TestModule()])
    return app


@pytest.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as async_client:
        yield async_client


class TestAccessLog:
    async def test_logs_one_entry_per_request(self, client: AsyncClient, mock_logger: Mock):
        await client.get("/probe")

        mock_logger.info.assert_called_once()

    async def test_entry_carries_request_details(self, client: AsyncClient, mock_logger: Mock):
        await client.get("/probe")

        assert mock_logger.info.call_args.args[0] == "request.completed"
        logged = mock_logger.info.call_args.kwargs
        assert logged["method"] == "GET"
        assert logged["path"] == "/probe"
        assert logged["status_code"] == 200
        assert logged["duration_ms"] >= 0

    async def test_entry_carries_error_status_codes(self, client: AsyncClient, mock_logger: Mock):
        await client.get("/absent")

        assert mock_logger.info.call_args.kwargs["status_code"] == 404


class TestMiddlewareOrdering:
    async def test_access_log_runs_after_request_id_is_bound(self, client: AsyncClient, mock_logger: Mock):
        await client.get("/probe")

        bind_call = next(index for index, call in enumerate(mock_logger.mock_calls) if call[0] == "bind_request_id")
        info_call = next(index for index, call in enumerate(mock_logger.mock_calls) if call[0] == "info")
        assert bind_call < info_call
