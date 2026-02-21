from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager

from injector import inject

from src.application.services.transaction_manager_base import TransactionManagerBase
from src.infrastructure.database.connection_factory_base import ConnectionFactoryBase


class TransactionManager(TransactionManagerBase):
    """Concrete implementation of TransactionManagerBase.

    Delegates begin_transaction() to the injected ConnectionFactory, which manages
    the shared session ContextVar that repositories automatically pick up via get_session().
    """

    @inject
    def __init__(self, connection_factory: ConnectionFactoryBase) -> None:
        """Initialise with a connection factory.

        Args:
            connection_factory: The database connection factory used to open and manage
                the shared transaction session.
        """
        self._connection_factory = connection_factory

    def begin_transaction(self) -> AbstractAsyncContextManager[Callable[[], Awaitable[None]]]:
        return self._connection_factory.begin_transaction()
