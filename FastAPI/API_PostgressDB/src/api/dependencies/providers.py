from injector import Binder, Module, provider, singleton
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.api.dependencies.bindings import auth as auth_bindings
from src.api.dependencies.bindings import user as user_bindings
from src.application.services.logger import Logger
from src.application.services.password_hasher import PasswordHasher
from src.application.services.token_service import TokenService
from src.application.services.transaction_context import TransactionContext
from src.application.services.user_context import UserContext
from src.config.settings import Settings, get_settings
from src.infrastructure.auth.bcrypt_password_hasher import BcryptPasswordHasher
from src.infrastructure.auth.jwt_token_service import JwtTokenService
from src.infrastructure.auth.request_user_context import RequestUserContext
from src.infrastructure.database.session import create_engine, create_session_factory
from src.infrastructure.database.sqlalchemy_transaction_context import SqlAlchemyTransactionContext
from src.infrastructure.di.request_scope import request
from src.infrastructure.di.typed_binder import TypedBinder
from src.infrastructure.logging.json_logger import JsonLogger


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
        typed_binder.bind_typed(TransactionContext).to(SqlAlchemyTransactionContext, scope=request)

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
    def provide_session(self, session_factory: async_sessionmaker[AsyncSession]) -> AsyncSession:
        # Request-scoped: every repository and the transaction context in one
        # request receive this same session (a shared unit of work). Disposed
        # at request end by the scope teardown via AsyncSession.aclose().
        return session_factory()
