from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager

from sqlalchemy.ext.asyncio import AsyncSession


class ConnectionFactoryBase(ABC):
    """Abstract base class for database connection factory."""

    @abstractmethod
    def get_session(self) -> AbstractAsyncContextManager[AsyncSession]:
        """Get an async database session as a context manager.

        Yields:
            AsyncSession: A session that commits on clean exit and rolls back on exception.

        Usage:
            async with connection_factory.get_session() as session:
                # Use session for database operations
                pass
        """
        pass

    @abstractmethod
    def begin_transaction(self) -> AbstractAsyncContextManager[None]:
        """Start a shared transaction scope for the current async context.

        While inside this context manager, every call to get_session() on this factory —
        from any repository — reuses the same underlying session instead of opening a new one.
        Commits on clean exit, rolls back on exception. The session is stored in a ContextVar
        so it is automatically picked up by injected repositories without any signature changes.

        Usage:
            async with self._connection_factory.begin_transaction():
                entity = await self._repo_a.get_by_id(some_id)
                result = await self._repo_b.create(some_entity)
                # Both committed atomically on exit, rolled back on any exception
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the database connection factory."""
        pass
