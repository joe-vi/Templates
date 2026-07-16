from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from src.infrastructure.di.request_scope import async_request_scope


async def request_scope(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Open the DI request scope for the duration of the request.

    Args:
        request: The incoming request.
        call_next: The next handler in the middleware chain.

    Returns:
        The response from the next handler.
    """
    async with async_request_scope():
        return await call_next(request)
