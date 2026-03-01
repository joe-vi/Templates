"""SQLAlchemy async connection factory and session management."""

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from contextvars import ContextVar

from injector import inject
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings as settings_module
from src.infrastructure.database import connection_factory_base

_active_session: ContextVar[AsyncSession | None] = ContextVar(
    "_active_session", default=None
)


class ConnectionFactory(connection_factory_base.ConnectionFactoryBase):
    """Factory for creating and managing database connections."""

    @inject
    def __init__(self, settings: settings_module.Settings) -> None:
        """Initialize the database engine and session factory.

        Args:
            settings: Application settings containing database configuration.
        """
        self._engine: AsyncEngine = create_async_engine(
            settings.database_url,
            echo=settings.is_sql_echo_enabled,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
        )
        self._session_factory: async_sessionmaker[AsyncSession] = (
            async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        )

    @asynccontextmanager
    async def get_session(
        self, is_readonly: bool = False
    ) -> AsyncIterator[AsyncSession]:
        active_session = _active_session.get()
        # Reuse the transaction session set by begin_transaction() if present;
        # flush on write so the caller sees its own changes within the block.
        if active_session is not None:
            yield active_session

            if not is_readonly:
                await active_session.flush()

            return

        async with self._session_factory() as session:
            if is_readonly:
                yield session
            else:
                async with session.begin():
                    yield session

    @asynccontextmanager
    async def begin_transaction(
        self,
    ) -> AsyncIterator[Callable[[], Awaitable[None]]]:
        async with self._session_factory() as session:
            async with session.begin():
                token = _active_session.set(session)
                should_rollback = False

                # Callers await rollback() to signal an intentional abort
                # without raising an exception (business-logic abort path).
                async def rollback() -> None:
                    nonlocal should_rollback
                    should_rollback = True

                try:
                    yield rollback
                    if should_rollback:
                        await session.rollback()
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    # Always clear the ContextVar so later get_session() calls
                    # open a fresh session instead of picking up the old one.
                    _active_session.reset(token)

    async def close(self) -> None:
        await self._engine.dispose()
