from contextlib import AbstractAsyncContextManager
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession


class ConnectionFactory(Protocol):
    """Hands repositories a session: a fresh short-lived one for reads, the request's write unit of work for data updates.

    An infrastructure-internal seam (not a hexagonal port): it exposes an
    ``AsyncSession`` directly, so it is SQLAlchemy-coupled and consumed only by
    repositories. A read session is closed as soon as its block exits, returning
    the pooled connection immediately (no lingering idle-in-transaction). A write
    session is the request-scoped write unit of work, whose outermost scope
    commits on a clean exit.
    """

    def read(self) -> AbstractAsyncContextManager[AsyncSession]:
        """Open a fresh short-lived read session.

        Returns:
            An async context manager yielding a session that is closed on block
            exit, releasing the pooled connection immediately.
        """
        ...

    def write(self) -> AbstractAsyncContextManager[AsyncSession]:
        """Open, or (within the same task) join, the write unit of work.

        Returns:
            An async context manager yielding the write session; the outermost
            scope commits on a clean exit and rolls back on exception.
        """
        ...
