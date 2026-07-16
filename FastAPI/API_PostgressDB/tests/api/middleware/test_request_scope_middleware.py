import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import Mock

import pytest
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import StreamingResponse
from httpx import ASGITransport, AsyncClient
from injector import Binder, Injector, InstanceProvider, Module, provider

from src.api.middleware import registration
from src.infrastructure.di.request_scope import request as request_scoped
from src.ports.logger import Logger

# Long enough for the middleware chain to reach its teardown if it is going to: the bug this
# guards against only appears once the background task or streaming body yields control.
_YIELD = 0.01


class Tracked:
    """Request-scoped probe recording whether it was used after the scope disposed it."""

    def __init__(self) -> None:
        self.is_closed = False
        self.is_used_after_disposal = False

    async def aclose(self) -> None:
        self.is_closed = True

    def use(self) -> None:
        if self.is_closed:
            self.is_used_after_disposal = True


@pytest.fixture
def tracked_instances() -> list[Tracked]:
    return []


@pytest.fixture
def test_app(tracked_instances: list[Tracked]) -> FastAPI:
    # InstanceProvider bypasses injector's isinstance check, which a non-runtime_checkable
    # Protocol port cannot satisfy.
    class TestModule(Module):
        def configure(self, binder: Binder) -> None:
            binder.bind(Logger, to=InstanceProvider(Mock(spec=Logger)))

        @request_scoped
        @provider
        def provide_tracked(self) -> Tracked:
            instance = Tracked()
            tracked_instances.append(instance)
            return instance

    app = FastAPI()

    @app.get("/background")
    async def background(background_tasks: BackgroundTasks, request: Request) -> dict[str, str]:
        tracked = request.app.state.injector.get(Tracked)

        async def work() -> None:
            await asyncio.sleep(_YIELD)
            tracked.use()

        background_tasks.add_task(work)
        return {"ok": "true"}

    @app.get("/background-raises")
    async def background_raises(background_tasks: BackgroundTasks, request: Request) -> dict[str, str]:
        request.app.state.injector.get(Tracked)

        async def work() -> None:
            await asyncio.sleep(_YIELD)
            raise RuntimeError("background task blew up")

        background_tasks.add_task(work)
        return {"ok": "true"}

    @app.get("/stream")
    async def stream(request: Request) -> StreamingResponse:
        tracked = request.app.state.injector.get(Tracked)

        async def body() -> AsyncGenerator[bytes]:
            yield b"first"
            await asyncio.sleep(_YIELD)
            tracked.use()
            yield b"second"

        return StreamingResponse(body())

    registration.register(app)
    app.state.injector = Injector([TestModule()])
    return app


@pytest.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as async_client:
        yield async_client


class TestScopeOutlivesTheResponse:
    async def test_background_task_is_not_disposed_underneath(self, client: AsyncClient, tracked_instances: list[Tracked]):
        await client.get("/background")

        assert tracked_instances[0].is_used_after_disposal is False

    async def test_streaming_body_is_not_disposed_underneath(self, client: AsyncClient, tracked_instances: list[Tracked]):
        response = await client.get("/stream")

        assert response.content == b"firstsecond"
        assert tracked_instances[0].is_used_after_disposal is False


class TestDisposal:
    async def test_scope_is_disposed_once_the_request_ends(self, client: AsyncClient, tracked_instances: list[Tracked]):
        await client.get("/background")

        assert tracked_instances[0].is_closed is True

    async def test_scope_is_disposed_even_when_a_background_task_raises(self, test_app: FastAPI, tracked_instances: list[Tracked]):
        # The exception escapes the app: it is re-raised after the response was sent, so no
        # middleware can turn it into a response.
        transport = ASGITransport(app=test_app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.get("/background-raises")

        assert tracked_instances[0].is_closed is True

    async def test_each_request_gets_its_own_instance(self, client: AsyncClient, tracked_instances: list[Tracked]):
        await client.get("/background")
        await client.get("/background")

        assert len(tracked_instances) == 2
        assert tracked_instances[0] is not tracked_instances[1]
