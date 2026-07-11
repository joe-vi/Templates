from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.config.settings import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    """Create the async database engine from settings.

    Args:
        settings: Application settings containing database configuration.

    Returns:
        A configured AsyncEngine. Dispose it on shutdown.
    """
    return create_async_engine(
        settings.database_url, echo=settings.is_sql_echo_enabled, pool_size=settings.pool_size, max_overflow=settings.max_overflow
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory bound to the given engine.

    Args:
        engine: The async engine the sessions should use.

    Returns:
        An async_sessionmaker producing AsyncSession instances.
    """
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
