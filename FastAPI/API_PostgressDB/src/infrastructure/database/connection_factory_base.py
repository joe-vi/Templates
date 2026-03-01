"""Abstract base class for the database connection factory."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager

from sqlalchemy.ext.asyncio import AsyncSession


class ConnectionFactoryBase(ABC):
    """Abstract base class for database connection factory."""

    @abstractmethod
    def get_session(
        self, is_readonly: bool = False
    ) -> AbstractAsyncContextManager[AsyncSession]:
        """Get an async database session as a context manager.

        Args:
            is_readonly: When True, skips the commit on clean exit. Use for
                read-only operations that do not need to persist changes.

        Yields:
            AsyncSession: A session that rolls back on exception. Commits on
                clean exit only when is_readonly is False.

        Usage:
            async with connection_factory.get_session() as session:
                # Use session for database operations
                pass
        """
        pass

    @abstractmethod
    def begin_transaction(
        self,
    ) -> AbstractAsyncContextManager[Callable[[], Awaitable[None]]]:
        """Start a shared transaction scope for the current async context.

        While inside this context manager, every call to get_session() on this
        factory — from any repository — reuses the same underlying session
        instead of opening a new one. Commits on clean exit, rolls back on
        exception. The session is stored in a ContextVar so it is
        automatically picked up by injected repositories without any signature
        changes.

        Yields:
            An async callable with no arguments. Awaiting it marks the
            transaction for rollback so no commit is issued when the block
            exits normally.

        Usage:
            async with self._connection_factory.begin_transaction() as rb:
                entity = await self._repo_a.get_by_id(some_id)
                result = await self._repo_b.create(some_entity)
                # Both committed atomically on exit, rolled back on rb()/exc
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the database connection factory."""
        pass
