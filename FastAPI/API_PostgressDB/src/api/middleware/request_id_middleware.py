import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from src.ports.logger import Logger

_REQUEST_ID_HEADER = "X-Request-ID"


async def request_id(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Bind the request's correlation id onto the logger and echo it back.

    Runs inside the DI request scope: the id is bound onto the request-scoped ``Logger``.

    Args:
        request: The incoming request.
        call_next: The next handler in the middleware chain.

    Returns:
        The response, with the ``X-Request-ID`` header set.
    """
    correlation_id = request.headers.get(_REQUEST_ID_HEADER) or str(uuid.uuid4())
    request.app.state.injector.get(Logger).bind_request_id(correlation_id)
    response = await call_next(request)
    response.headers[_REQUEST_ID_HEADER] = correlation_id
    return response
