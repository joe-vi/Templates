from fastapi import FastAPI

from src.api.middleware.access_log_middleware import access_log
from src.api.middleware.exception_handler_middleware import exception_handler
from src.api.middleware.request_id_middleware import request_id
from src.api.middleware.request_scope_middleware import RequestScopeMiddleware


def register(app: FastAPI) -> None:
    """Register the HTTP middlewares, outermost last.

    Starlette runs the most recently registered middleware first, so ``RequestScopeMiddleware`` is
    registered last to sit outermost: ``request_id`` binds the request-scoped ``Logger`` and needs
    the scope already open. ``exception_handler`` is innermost, so the 500 it returns for a failed
    request still travels back out through ``access_log``, which records it, and through
    ``request_id``, which stamps the correlation header on it.

    Args:
        app: The application to register the middlewares on.
    """
    app.middleware("http")(exception_handler)
    app.middleware("http")(access_log)
    app.middleware("http")(request_id)
    app.add_middleware(RequestScopeMiddleware)
