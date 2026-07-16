from fastapi import FastAPI

from src.api.middleware.access_log_middleware import access_log
from src.api.middleware.request_id_middleware import request_id
from src.api.middleware.request_scope_middleware import request_scope


def register(app: FastAPI) -> None:
    """Register the HTTP middlewares, outermost last.

    Starlette runs the most recently registered middleware first, so ``request_scope`` is
    registered last to sit outermost: ``request_id`` binds the request-scoped ``Logger`` and
    needs the scope already open. ``access_log`` is innermost — it logs once the correlation id
    is bound and the route's guard has populated the ``UserContext``.

    Args:
        app: The application to register the middlewares on.
    """
    app.middleware("http")(access_log)
    app.middleware("http")(request_id)
    app.middleware("http")(request_scope)
