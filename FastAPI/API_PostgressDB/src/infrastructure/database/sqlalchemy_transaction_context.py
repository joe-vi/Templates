from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from injector import inject
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.transaction_context import Transaction, TransactionContext


class SqlAlchemyTransaction(Transaction):
    """``Transaction`` commit handle over the request-scoped session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._is_committed = False

    @property
    def is_committed(self) -> bool:
        return self._is_committed

    async def commit(self) -> None:
        await self._session.commit()
        self._is_committed = True


class SqlAlchemyTransactionContext(TransactionContext):
    """``TransactionContext`` adapter backed by the request-scoped ``AsyncSession``.

    Repositories built for the same request hold this same session, so every
    repository call inside a ``begin()`` block joins one transaction.
    ``commit()`` is only reachable on the all-success path, so committing a
    partially-failed unit of work is structurally impossible (unlike designs
    that auto-commit on clean exit).
    """

    @inject
    def __init__(self, session: AsyncSession) -> None:
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
