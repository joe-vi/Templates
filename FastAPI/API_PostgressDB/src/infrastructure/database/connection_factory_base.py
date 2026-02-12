from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager

from sqlalchemy.ext.asyncio import AsyncSession


class ConnectionFactoryBase(ABC):
    """Abstract base class for database connection factory."""

    @abstractmethod
    def get_session(self) -> AbstractAsyncContextManager[AsyncSession]:
        """
        Get an async database session as a context manager.

        Yields:
            AsyncSession: An async SQLAlchemy session

        Usage:
            async with connection_factory.get_session() as session:
                # Use session for database operations
                pass
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the database connection factory."""
        pass
