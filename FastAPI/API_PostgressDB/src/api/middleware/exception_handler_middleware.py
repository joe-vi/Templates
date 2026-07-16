from collections.abc import Awaitable, Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from src.ports.logger import Logger

_INTERNAL_ERROR_DETAIL = "Internal Server Error"


async def exception_handler(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Turn any exception escaping the route into a logged 500 response.

    Runs innermost, so no handler below needs a ``try``/``except`` merely to report a failure.
    ``HTTPException`` and request validation errors never reach it — Starlette's own exception
    middleware resolves those into responses first.

    Args:
        request: The incoming request.
        call_next: The next handler in the middleware chain.

    Returns:
        The response from the next handler, or a 500 response when it raised.
    """
    try:
        return await call_next(request)
    except Exception as exception:
        _log_unhandled(request, exception)
        return _internal_error_response()


def _log_unhandled(request: Request, exception: Exception) -> None:
    request.app.state.injector.get(Logger).error(
        "request.unhandled_exception", exception=exception, method=request.method, path=request.url.path
    )


def _internal_error_response() -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": _INTERNAL_ERROR_DETAIL})
