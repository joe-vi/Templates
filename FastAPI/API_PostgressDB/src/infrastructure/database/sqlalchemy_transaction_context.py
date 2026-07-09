"""SQLAlchemy adapter implementing the transaction context port."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from injector import inject
from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyTransaction:
    """Commit handle over the request-scoped session."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the transaction handle.

        Args:
            session: The request-scoped session whose transaction this
                handle commits.
        """
        self._session = session
        self._is_committed = False

    @property
    def is_committed(self) -> bool:
        return self._is_committed

    async def commit(self) -> None:
        await self._session.commit()
        self._is_committed = True


class SqlAlchemyTransactionContext:
    """Transaction context backed by the request-scoped ``AsyncSession``.

    Repositories built for the same request hold this same session, so every
    repository call inside a ``begin()`` block joins one transaction.

    Rollback-unless-committed: a failed repository operation leaves the
    session's transaction unusable until rolled back, and ``commit()`` is only
    reachable on the all-success path — so committing a partially-failed unit
    of work is structurally impossible (unlike designs that auto-commit on
    clean exit).
    """

    @inject
    def __init__(self, session: AsyncSession) -> None:
        """Initialize the transaction context.

        Args:
            session: The request-scoped async session shared with every
                repository adapter in the same request.
        """
        self._session = session

    @asynccontextmanager
    async def begin(self) -> AsyncIterator[SqlAlchemyTransaction]:
        transaction = SqlAlchemyTransaction(self._session)
        try:
            yield transaction
        except Exception:
            await self._session.rollback()
            raise
        else:
            if not transaction.is_committed:
                await self._session.rollback()
