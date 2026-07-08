"""FastAPI application entry point and lifecycle management."""

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from dishka import make_async_container
from dishka.integrations.fastapi import FastapiProvider, setup_dishka
from fastapi import FastAPI, Request, Response

from src.api.dependencies.providers import AppProvider
from src.api.routers.auth import auth_routes
from src.api.routers.user import user_routes
from src.infrastructure.logging import log_context

# The dependency graph is validated here — a missing binding fails at import,
# not mid-request. APP-scoped resources (the engine) are finalised by
# container.close() in the lifespan shutdown.
container = make_async_container(AppProvider(), FastapiProvider())


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage the application startup and shutdown lifecycle.

    Args:
        app: The FastAPI application instance.

    Yields:
        None. On shutdown, closes the container, finalising APP-scoped
        resources (disposes the database engine).
    """
    yield
    await app.state.dishka_container.close()


app = FastAPI(
    title="FastAPI Clean Architecture Template",
    description="FastAPI Clean Architecture with async SQLAlchemy",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def add_request_id(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Scope the log-correlation context variables to this request.

    request_id is set here; user_id is cleared so a value can never leak
    between requests handled in the same task (e.g. under test transports),
    then populated by the JWT guard once the caller is authenticated.
    """
    request_id_token = log_context.request_id_var.set(str(uuid.uuid4()))
    user_id_token = log_context.user_id_var.set(None)
    try:
        return await call_next(request)
    finally:
        log_context.user_id_var.reset(user_id_token)
        log_context.request_id_var.reset(request_id_token)


app.include_router(auth_routes.router)
app.include_router(user_routes.router)
setup_dishka(container, app)


@app.get("/")
async def root() -> dict[str, str]:
    """Return application information with links to API documentation.

    Returns:
        A dictionary containing a welcome message and documentation URLs.
    """
    return {
        "message": "Welcome to FastAPI Clean Architecture Template",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return the application health status.

    Returns:
        A dictionary containing the health status.
    """
    return {"status": "healthy"}
