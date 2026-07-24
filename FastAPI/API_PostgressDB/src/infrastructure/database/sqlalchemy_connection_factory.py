from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from injector import inject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infrastructure.database.connection_factory import ConnectionFactory
from src.infrastructure.database.sqlalchemy_transaction_context import SqlAlchemyTransactionContext


class SqlAlchemyConnectionFactory(ConnectionFactory):
    """``ConnectionFactory`` adapter backed by SQLAlchemy async sessions.

    A read session is closed as soon as its block exits, returning the pooled
    connection immediately (no lingering idle-in-transaction). A write session is
    the request-scoped write unit of work from ``SqlAlchemyTransactionContext``,
    whose outermost scope commits on a clean exit.
    """

    @inject
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], transaction_context: SqlAlchemyTransactionContext) -> None:
        self._session_factory = session_factory
        self._transaction_context = transaction_context

    @asynccontextmanager
    async def read(self) -> AsyncGenerator[AsyncSession]:
        session = self._session_factory()
        try:
            yield session
        finally:
            await session.close()

    @asynccontextmanager
    async def write(self) -> AsyncGenerator[AsyncSession]:
        async with self._transaction_context.begin():
            yield self._transaction_context.session
