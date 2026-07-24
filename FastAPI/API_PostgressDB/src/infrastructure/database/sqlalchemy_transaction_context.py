import contextvars
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from injector import inject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.ports.transaction_context import Transaction, TransactionContext


@dataclass
class _WriteUnit:
    session: AsyncSession
    rolled_back: bool = False


class SqlAlchemyTransaction(Transaction):
    def __init__(self, context: "SqlAlchemyTransactionContext") -> None:
        self._context = context

    async def rollback(self) -> None:
        await self._context.rollback()


class SqlAlchemyTransactionContext(TransactionContext):
    @inject
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        # Per-task: set inside begin(), so parallel tasks sharing this context each get their own unit.
        self._unit: contextvars.ContextVar[_WriteUnit | None] = contextvars.ContextVar("write_unit", default=None)

    @property
    def session(self) -> AsyncSession:
        unit = self._unit.get()
        if unit is None:
            raise RuntimeError("session is only available inside an active begin() scope")
        return unit.session

    async def rollback(self) -> None:
        unit = self._unit.get()
        if unit is not None and not unit.rolled_back:
            await unit.session.rollback()
            unit.rolled_back = True

    @asynccontextmanager
    async def begin(self) -> AsyncGenerator[SqlAlchemyTransaction]:
        parent = self._unit.get()
        if parent is not None:
            # A rolled-back unit is dead: refuse further writes instead of running on a fresh transaction.
            if parent.rolled_back:
                raise RuntimeError("write unit already rolled back by an earlier failure; no further writes are allowed")
            # Nested: join the open unit; roll the whole unit back if a write fails so nothing partial commits.
            try:
                yield SqlAlchemyTransaction(self)
            except Exception:
                await self.rollback()
                raise
            return

        session = self._session_factory()
        try:
            await session.begin()
            unit = _WriteUnit(session=session)
            token = self._unit.set(unit)
            try:
                yield SqlAlchemyTransaction(self)
            except Exception:
                if not unit.rolled_back:
                    await session.rollback()
                raise
            else:
                if not unit.rolled_back:
                    await session.commit()
            finally:
                self._unit.reset(token)
        finally:
            await session.close()
