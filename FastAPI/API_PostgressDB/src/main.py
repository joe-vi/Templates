import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from injector import Injector
from sqlalchemy.ext.asyncio import AsyncEngine

from src.api.dependencies.providers import AppModule
from src.api.routers import auth, user
from src.infrastructure.di.request_scope import async_request_scope
from src.infrastructure.logging import log_context

injector = Injector([AppModule()])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage the application startup and shutdown lifecycle.

    On shutdown, disposes the database engine (singletons are not covered by
    the request-scope teardown).
    """
    yield
    engine = app.state.injector.get(AsyncEngine)
    await engine.dispose()


app = FastAPI(
    title="FastAPI Clean Architecture Template",
    description="FastAPI Clean Architecture with async SQLAlchemy",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.injector = injector


@app.middleware("http")
async def request_context(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Open the DI request scope and the log-correlation context.

    Every request-scoped dependency resolved while handling this request is
    cached for the request and disposed when it ends. request_id is set here;
    user_id is cleared so a value can never leak between requests handled in
    the same task, then populated by the JWT guard once the caller is
    authenticated.
    """
    request_id_token = log_context.request_id_var.set(str(uuid.uuid4()))
    user_id_token = log_context.user_id_var.set(None)
    try:
        async with async_request_scope():
            return await call_next(request)
    finally:
        log_context.user_id_var.reset(user_id_token)
        log_context.request_id_var.reset(request_id_token)


app.include_router(auth.router)
app.include_router(user.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Return application information with links to API documentation."""
    return {"message": "Welcome to FastAPI Clean Architecture Template", "docs": "/docs", "redoc": "/redoc"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return the application health status."""
    return {"status": "healthy"}
