from contextlib import AbstractAsyncContextManager
from typing import Protocol


class Transaction(Protocol):
    """Handle to the unit of work opened by ``TransactionContext.begin()``."""

    async def rollback(self) -> None:
        """Immediately roll back the whole unit of work.

        Call this when a nested write reports a failure through a benign result
        enum (one that raised no exception), so the enclosing ``begin()`` will not
        commit; do not perform further data updates in the same unit — they will
        not be persisted.
        """
        ...


class TransactionContext(Protocol):
    """Reentrant, per-task write unit of work spanning one or more repository writes.

    Use in a use case only when several writes must succeed or fail together; a
    single write self-commits without an explicit scope. Each outermost ``begin()``
    owns one session, created on entry and closed on exit. Reentrancy is per
    asyncio task: a nested ``begin()`` in the same task joins the open unit, while
    concurrent tasks each get their own session — so use cases may run in parallel
    through one shared context.

    A DB error escaping a nested write rolls the whole unit back automatically, so
    a repository may translate it into a result enum without the clean exit
    committing a poisoned transaction. A benign failure result that raises no
    exception is not detected: roll back explicitly if it must abort the unit.
    """

    async def rollback(self) -> None:
        """Immediately roll back the current unit of work.

        The outermost ``begin()`` then will not commit; further updates in the
        same unit are not persisted.
        """
        ...

    def begin(self) -> AbstractAsyncContextManager[Transaction]:
        """Open, or (within the same task) join, the write unit of work.

        Returns:
            An async context manager yielding a Transaction. The outermost scope
            commits on a clean exit and rolls back on exception or after
            ``rollback()``; a nested scope joins the open unit and neither commits
            nor closes.
        """
        ...
