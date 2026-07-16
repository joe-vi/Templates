from starlette.types import ASGIApp, Receive, Scope, Send

from src.infrastructure.di.request_scope import async_request_scope


class RequestScopeMiddleware:
    """Pure ASGI middleware, deliberately not a ``BaseHTTPMiddleware`` dispatch function.

    ``BaseHTTPMiddleware``'s ``call_next`` returns as soon as the response starts, which would end
    the scope while background tasks and streaming response bodies are still running: they hold a
    copied context that still resolves the disposed instances, so the session would be reused after
    ``aclose()`` and its connection leaked. Wrapping the raw ASGI call instead keeps the scope open
    until the whole request — background work included — has finished.
    """

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Open the DI request scope for the duration of the request.

        Args:
            scope: The ASGI connection scope.
            receive: The ASGI receive callable.
            send: The ASGI send callable.
        """
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        async with async_request_scope():
            await self._app(scope, receive, send)
