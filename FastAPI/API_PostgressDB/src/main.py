from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from injector import Injector
from sqlalchemy.ext.asyncio import AsyncEngine

from src.api.dependencies.providers import AppModule
from src.api.middleware import request_context
from src.api.routers.auth.router import router as auth_router
from src.api.routers.user.router import router as user_router
from src.config.settings import Settings
from src.infrastructure.logging.json_logger import configure_logging

injector = Injector([AppModule()])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage the application startup and shutdown lifecycle."""
    configure_logging(app.state.injector.get(Settings))
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
app.middleware("http")(request_context)

app.include_router(auth_router)
app.include_router(user_router)


@app.get("/")
async def root() -> dict[str, str]:
    """Return application information with links to API documentation."""
    return {"message": "Welcome to FastAPI Clean Architecture Template", "docs": "/docs", "redoc": "/redoc"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return the application health status."""
    return {"status": "healthy"}
