"""Request-scoped database session dependency."""

from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped async session.

    The session factory is created once at startup and stored on
    ``app.state.session_factory`` (see ``main.lifespan``). FastAPI caches this
    dependency per request, so every adapter resolved within one request shares
    the same session — a natural per-request unit of work, with no module-level
    session state.

    Args:
        request: The incoming request, used to reach ``app.state``.

    Yields:
        An AsyncSession that is closed when the request finishes.
    """
    session_factory: async_sessionmaker[AsyncSession] = (
        request.app.state.session_factory
    )
    async with session_factory() as session:
        yield session
