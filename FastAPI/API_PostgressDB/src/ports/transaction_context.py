from contextlib import AbstractAsyncContextManager
from typing import Protocol


class Transaction(Protocol):
    """Handle to the transaction opened by ``TransactionContext.begin()``."""

    async def commit(self) -> None:
        """Persist all work performed inside the ``begin()`` block."""
        ...


class TransactionContext(Protocol):
    """Port for a unit of work spanning one or more repository calls."""

    def begin(self) -> AbstractAsyncContextManager[Transaction]:
        """Open a transaction scope.

        Returns:
            An async context manager yielding a Transaction. On exit the
            transaction is rolled back unless ``commit()`` was called.
        """
        ...
