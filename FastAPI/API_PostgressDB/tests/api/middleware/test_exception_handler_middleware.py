from collections.abc import AsyncGenerator
from unittest.mock import Mock

import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from injector import Binder, Injector, InstanceProvider, Module

from src.api.middleware import registration
from src.ports.logger import Logger

_BOOM = "boom"


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

    @app.get("/explode")
    async def explode() -> dict[str, str]:
        raise RuntimeError(_BOOM)

    @app.get("/teapot")
    async def teapot() -> dict[str, str]:
        raise HTTPException(status_code=418, detail="I'm a teapot")

    registration.register(app)
    app.state.injector = Injector([TestModule()])
    return app


@pytest.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as async_client:
        yield async_client


class TestExceptionHandler:
    async def test_uncaught_exception_becomes_500(self, client: AsyncClient):
        response = await client.get("/explode")

        assert response.status_code == 500

    async def test_response_body_hides_the_exception_detail(self, client: AsyncClient):
        response = await client.get("/explode")

        assert response.json() == {"detail": "Internal Server Error"}
        assert _BOOM not in response.text

    async def test_exception_is_logged_with_request_details(self, client: AsyncClient, mock_logger: Mock):
        await client.get("/explode")

        mock_logger.error.assert_called_once()
        assert mock_logger.error.call_args.args[0] == "request.unhandled_exception"
        logged = mock_logger.error.call_args.kwargs
        assert isinstance(logged["exception"], RuntimeError)
        assert logged["method"] == "GET"
        assert logged["path"] == "/explode"

    async def test_http_exception_is_left_to_fastapi(self, client: AsyncClient, mock_logger: Mock):
        response = await client.get("/teapot")

        assert response.status_code == 418
        mock_logger.error.assert_not_called()

    async def test_successful_request_is_untouched(self, client: AsyncClient, mock_logger: Mock):
        response = await client.get("/teapot")

        assert response.json() == {"detail": "I'm a teapot"}
        mock_logger.error.assert_not_called()


class TestMiddlewareOrdering:
    async def test_failed_request_still_gets_an_access_entry(self, client: AsyncClient, mock_logger: Mock):
        await client.get("/explode")

        assert mock_logger.info.call_args.args[0] == "request.completed"
        assert mock_logger.info.call_args.kwargs["status_code"] == 500

    async def test_failed_request_still_gets_the_correlation_header(self, client: AsyncClient):
        response = await client.get("/explode")

        assert response.headers["X-Request-ID"]

    async def test_exception_is_logged_after_the_request_id_is_bound(self, client: AsyncClient, mock_logger: Mock):
        await client.get("/explode")

        bind_call = next(index for index, call in enumerate(mock_logger.mock_calls) if call[0] == "bind_request_id")
        error_call = next(index for index, call in enumerate(mock_logger.mock_calls) if call[0] == "error")
        assert bind_call < error_call
