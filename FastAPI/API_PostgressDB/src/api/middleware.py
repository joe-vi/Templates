import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from src.application.services.logger import Logger
from src.infrastructure.di.request_scope import async_request_scope

_REQUEST_ID_HEADER = "X-Request-ID"


async def request_context(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Open the DI request scope and bind the request's correlation id.

    Args:
        request: The incoming request.
        call_next: The next handler in the middleware chain.

    Returns:
        The response, with the ``X-Request-ID`` header set.
    """
    request_id = request.headers.get(_REQUEST_ID_HEADER) or str(uuid.uuid4())
    async with async_request_scope():
        request.app.state.injector.get(Logger).bind_request_id(request_id)
        response = await call_next(request)
    response.headers[_REQUEST_ID_HEADER] = request_id
    return response
