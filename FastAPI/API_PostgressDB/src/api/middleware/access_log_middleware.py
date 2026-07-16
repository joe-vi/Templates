import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from src.ports.logger import Logger


async def access_log(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Emit one structured access entry per request through the request-scoped ``Logger``.

    Replaces uvicorn's access log, which runs outside the DI request scope and so cannot carry
    the correlation fields. Runs inside the scope and after the route's guard, so the entry
    carries the bound ``request_id`` and, on authenticated routes, the caller's ``user_id``.

    Args:
        request: The incoming request.
        call_next: The next handler in the middleware chain.

    Returns:
        The response returned by the downstream handler.
    """
    started_at = time.perf_counter()
    response = await call_next(request)
    request.app.state.injector.get(Logger).info(
        "request.completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=_elapsed_ms(started_at),
    )
    return response


def _elapsed_ms(started_at: float) -> float:
    return round((time.perf_counter() - started_at) * 1000, 2)
