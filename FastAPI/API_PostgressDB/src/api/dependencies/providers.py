from injector import Binder, Module, provider, singleton
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.api.dependencies.bindings import auth as auth_bindings
from src.api.dependencies.bindings import user as user_bindings
from src.config.settings import Settings, get_settings
from src.infrastructure.auth.bcrypt_password_hasher import BcryptPasswordHasher
from src.infrastructure.auth.jwt_token_service import JwtTokenService
from src.infrastructure.auth.request_user_context import RequestUserContext
from src.infrastructure.database.connection_factory import ConnectionFactory
from src.infrastructure.database.session import create_engine, create_session_factory
from src.infrastructure.database.sqlalchemy_connection_factory import SqlAlchemyConnectionFactory
from src.infrastructure.database.sqlalchemy_transaction_context import SqlAlchemyTransactionContext
from src.infrastructure.di.request_scope import request
from src.infrastructure.di.typed_binder import TypedBinder
from src.infrastructure.logging.json_logger import JsonLogger
from src.ports.logger import Logger
from src.ports.password_hasher import PasswordHasher
from src.ports.token_service import TokenService
from src.ports.transaction_context import TransactionContext
from src.ports.user_context import UserContext


class AppModule(Module):
    """Composition root: binds every port to its adapter with an explicit scope."""

    def configure(self, binder: Binder) -> None:
        """Declare the cross-cutting bindings and delegate each domain's to its ``register()``."""
        typed_binder = TypedBinder(binder)

        # Stateless services — one instance per process.
        typed_binder.bind_typed(PasswordHasher).to(BcryptPasswordHasher, scope=singleton)
        typed_binder.bind_typed(TokenService).to(JwtTokenService, scope=singleton)

        # Per-request collaborators holding request state.
        typed_binder.bind_typed(Logger).to(JsonLogger, scope=request)
        typed_binder.bind_typed(UserContext).to(RequestUserContext, scope=request)

        # Unit of work: the write scope (SqlAlchemyTransactionContext) is request-scoped — one write
        # session per request — bound to itself and to the TransactionContext port via the two
        # providers below (both returning the same instance). The ConnectionFactory adapter is
        # stateless, so it stays transient and shares that one scope.
        typed_binder.bind_typed(ConnectionFactory).to(SqlAlchemyConnectionFactory)

        # Per-domain repositories and use cases (transient).
        user_bindings.register(typed_binder)
        auth_bindings.register(typed_binder)

    @singleton
    @provider
    def provide_settings(self) -> Settings:
        return get_settings()

    @singleton
    @provider
    def provide_engine(self, settings: Settings) -> AsyncEngine:
        # Disposed explicitly in main.lifespan shutdown (singletons are not
        # covered by request-scope disposal).
        return create_engine(settings)

    @singleton
    @provider
    def provide_session_factory(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return create_session_factory(engine)

    @request
    @provider
    def provide_transaction_context(self, session_factory: async_sessionmaker[AsyncSession]) -> SqlAlchemyTransactionContext:
        # Request-scoped write unit of work. Its session is created and closed per outermost
        # begin(); the instance holds no session between scopes (unit lives in a per-task ContextVar).
        return SqlAlchemyTransactionContext(session_factory)

    @request
    @provider
    def provide_transaction_context_port(self, scope: SqlAlchemyTransactionContext) -> TransactionContext:
        # The port and the concrete must resolve to the same per-request instance so a use case's
        # begin() and the repository's ConnectionFactory.write() nest on one write session; returning
        # the concrete keeps them identical.
        return scope
