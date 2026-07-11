from contextlib import AbstractAsyncContextManager
from typing import Protocol


class Transaction(Protocol):
    """Handle to the transaction opened by ``TransactionContext.begin()``."""

    async def commit(self) -> None:
        """Persist all work performed inside the ``begin()`` block.

        Call exactly once, only after every operation in the block has
        reported success.
        """
        ...


class TransactionContext(Protocol):
    """Port for atomic units of work spanning one or more repositories.

    Every repository in a request shares one database session, so all
    repository calls inside a single ``begin()`` block — across any number of
    repositories — join the same transaction and succeed or fail together.

    Semantics are *rollback unless committed*: leaving the ``begin()`` block
    without having called ``commit()`` — whether by early return on a failure
    result or by an exception — rolls back every operation performed inside
    it. This makes partial commits impossible: a use case can only commit
    after it has seen every repository call succeed.

    Usage (single repository):
        async with self._transaction_context.begin() as transaction:
            result, entity_id = await self._repository.create(entity)
            if result is CreateResult.SUCCESS:
                await transaction.commit()
        return (result, entity_id)

    Usage (atomic multi-repository operation):
        async with self._transaction_context.begin() as transaction:
            result_a, order_id = await self._order_repository.create(order)
            if result_a is not CreateResult.SUCCESS:
                return (result_a, None)
            result_b = await self._stock_repository.decrement(item_id)
            if result_b is not UpdateResult.SUCCESS:
                return (CreateResult.FAILURE, None)  # order rolls back too
            await transaction.commit()
        return (result_a, order_id)
    """

    def begin(self) -> AbstractAsyncContextManager[Transaction]:
        """Open a transaction scope over the request's shared session.

        Returns:
            An async context manager yielding a Transaction. On exit the
            transaction is rolled back unless ``commit()`` was called.
        """
        ...
