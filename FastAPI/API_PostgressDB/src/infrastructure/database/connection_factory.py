from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.config.settings import Settings
from src.infrastructure.database.connection_factory_base import ConnectionFactoryBase


class ConnectionFactory(ConnectionFactoryBase):
    """Factory for creating and managing database connections."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the database engine and session factory.

        Args:
            settings: The application settings containing database configuration.
        """
        self._engine: AsyncEngine = create_async_engine(
            settings.database_url,
            echo=settings.is_sql_echo_enabled,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
        )
        self._session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncIterator[AsyncSession]:
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def close(self) -> None:
        await self._engine.dispose()
