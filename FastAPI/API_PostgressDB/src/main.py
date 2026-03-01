"""FastAPI application entry point and lifecycle management."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_injector import InjectorMiddleware, attach_injector

from src import container
from src.api.routers.auth import auth_routes
from src.api.routers.user import user_routes
from src.infrastructure.database import connection_factory_base


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage the application startup and shutdown lifecycle.

    Args:
        app: The FastAPI application instance.

    Yields:
        None. On shutdown, disposes database connections.
    """
    yield

    connection_factory = container.injector.get(
        connection_factory_base.ConnectionFactoryBase
    )
    await connection_factory.close()


app = FastAPI(
    title="FastAPI Clean Architecture Template",
    description="FastAPI Clean Architecture with async SQLAlchemy",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(InjectorMiddleware, injector=container.injector)
attach_injector(app, container.injector)

app.include_router(auth_routes.router)
app.include_router(user_routes.router)


@app.get("/")
async def root():
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
async def health_check():
    """Return the application health status.

    Returns:
        A dictionary containing the health status.
    """
    return {"status": "healthy"}
