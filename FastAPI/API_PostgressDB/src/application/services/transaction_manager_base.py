"""Abstract base class for the transaction manager."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager


class TransactionManagerBase(ABC):
    """Abstract base class for managing atomic database transactions."""

    @abstractmethod
    def begin_transaction(
        self,
    ) -> AbstractAsyncContextManager[Callable[[], Awaitable[None]]]:
        """Start a shared transaction scope for the current async context.

        While inside this context manager, every call to get_session() on any
        injected repository reuses the same underlying session instead of
        opening a new one. Commits on clean exit and rolls back on any
        exception.

        The context manager yields a rollback callable. Calling it signals the
        transaction to roll back on exit without raising an exception — useful
        when a use case needs to abort based on business logic rather than an
        error condition.

        Yields:
            An async callable with no arguments. Awaiting it marks the
            transaction for rollback so no commit is issued when the block
            exits normally.

        Usage:
            async with self._transaction_manager.begin_transaction() as rb:
                entity = await self._repo_a.get_by_id(some_id)
                if not entity.is_eligible:
                    await rb()  # abort without raising
                    return
                result = await self._repo_b.create(some_entity)
                # Committed atomically on exit, rolled back on rb()/exception
        """
        pass
