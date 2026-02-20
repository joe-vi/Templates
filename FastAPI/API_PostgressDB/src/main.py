from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_injector import attach_injector

from src.api.routers.greeting.greeting_routes import router as greeting_router
from src.application.services.blob_storage_service_base import BlobStorageServiceBase
from src.container import injector
from src.infrastructure.database.connection_factory_base import ConnectionFactoryBase


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the application startup and shutdown lifecycle.

    Args:
        app: The FastAPI application instance.

    Yields:
        None. On shutdown, disposes database connections.
    """
    yield

    # Cleanup: Close database connections and external service clients
    connection_factory = injector.get(ConnectionFactoryBase)
    await connection_factory.close()

    blob_storage_service = injector.get(BlobStorageServiceBase)
    await blob_storage_service.close()


app = FastAPI(
    title="FastAPI Clean Architecture Template",
    description="A FastAPI application using Clean Architecture with async SQLAlchemy",
    version="1.0.0",
    lifespan=lifespan,
)

# Attach injector as middleware for dependency injection
attach_injector(app, injector)

app.include_router(greeting_router)


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
