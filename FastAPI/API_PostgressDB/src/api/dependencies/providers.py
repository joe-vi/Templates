"""Composition root: injector module wiring ports to adapters.

``TypedBinder`` makes each binding a one-liner declaring implementation,
port, and scope — and a binding whose implementation does not satisfy its
port is a type-checker error at that line. There is no graph-completeness
check: a missing binding surfaces as a runtime error on first resolution.

Scopes:
    singleton — one instance for the process (engine, stateless services).
    request   — one instance per HTTP request (session, repositories,
                transaction context, use cases). Everything in a request
                shares the same ``AsyncSession``, which is what makes a
                multi-repository ``TransactionContext.begin()`` block atomic.
                The request scope also disposes its objects on request end
                (the session is closed via ``aclose()``).
"""

from injector import Binder, Module, provider, singleton
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.api.dependencies.injection import TypedBinder, request
from src.application.services.logger import Logger
from src.application.services.password_hasher import PasswordHasher
from src.application.services.token_service import TokenService
from src.application.services.transaction_context import TransactionContext
from src.application.use_cases.auth.auth_use_case import AuthUseCase
from src.application.use_cases.user.user_use_case import UserUseCase
from src.config.settings import Settings, get_settings
from src.domain.repositories.user.user_repository import UserRepository
from src.infrastructure.auth.bcrypt_password_hasher import BcryptPasswordHasher
from src.infrastructure.auth.jwt_token_service import JwtTokenService
from src.infrastructure.database.session import (
    create_engine,
    create_session_factory,
)
from src.infrastructure.database.sqlalchemy_transaction_context import (
    SqlAlchemyTransactionContext,
)
from src.infrastructure.logging.json_logger import JsonLogger
from src.infrastructure.repositories.user.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)


class AppModule(Module):
    """Binds every port to its adapter with an explicit scope."""

    def configure(self, binder: Binder) -> None:
        """Declare all interface–implementation bindings."""
        typed_binder = TypedBinder(binder)

        # Stateless services — one instance per process.
        typed_binder.bind_typed(PasswordHasher).to(
            BcryptPasswordHasher, scope=singleton
        )
        typed_binder.bind_typed(TokenService).to(
            JwtTokenService, scope=singleton
        )
        typed_binder.bind_typed(Logger).to(JsonLogger, scope=singleton)

        # Per-request collaborators — auto-wired from constructor type hints.
        typed_binder.bind_typed(UserRepository).to(
            SqlAlchemyUserRepository, scope=request
        )
        typed_binder.bind_typed(TransactionContext).to(
            SqlAlchemyTransactionContext, scope=request
        )
        typed_binder.bind_self_typed(UserUseCase, scope=request)
        typed_binder.bind_self_typed(AuthUseCase, scope=request)

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
    def provide_session_factory(
        self, engine: AsyncEngine
    ) -> async_sessionmaker[AsyncSession]:
        return create_session_factory(engine)

    @request
    @provider
    def provide_session(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> AsyncSession:
        # Request-scoped: every repository and the transaction context in one
        # request receive this same session (a shared unit of work). Disposed
        # at request end by the scope teardown via AsyncSession.aclose().
        return session_factory()
