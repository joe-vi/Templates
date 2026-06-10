"""FastAPI application entry point and lifecycle management."""

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from src.api.routers.auth import auth_routes
from src.api.routers.user import user_routes
from src.config.settings import get_settings
from src.infrastructure.database.session import (
    create_engine,
    create_session_factory,
)
from src.infrastructure.logging import log_context


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage the application startup and shutdown lifecycle.

    Creates the database engine and session factory on startup, stores the
    factory on ``app.state`` for the request-scoped session dependency, and
    disposes the engine on shutdown.

    Args:
        app: The FastAPI application instance.

    Yields:
        None.
    """
    settings = get_settings()
    engine = create_engine(settings)
    app.state.session_factory = create_session_factory(engine)
    try:
        yield
    finally:
        await engine.dispose()


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
    """Tag each request with a unique id for log correlation."""
    token = log_context.request_id_var.set(str(uuid.uuid4()))
    try:
        return await call_next(request)
    finally:
        log_context.request_id_var.reset(token)


app.include_router(auth_routes.router)
app.include_router(user_routes.router)


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
