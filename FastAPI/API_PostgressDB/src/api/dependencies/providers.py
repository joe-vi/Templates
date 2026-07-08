"""Composition root: Dishka provider wiring ports to adapters.

One declarative binding per dependency — implementation, port, and scope in a
single line. Constructor arguments are auto-wired from type hints, injectable
classes carry no decorators, and the dependency graph is validated when the
container is created (see ``main.py``), so a missing binding fails at startup
rather than mid-request.

Scopes:
    Scope.APP     — one instance for the process (engine, stateless services).
    Scope.REQUEST — one instance per HTTP request (session, repositories,
                    transaction context, use cases). Everything in a request
                    shares the same ``AsyncSession``, which is what makes a
                    multi-repository ``TransactionContext.begin()`` block
                    atomic.
"""

from collections.abc import AsyncIterable

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

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


class AppProvider(Provider):
    """Binds every port to its adapter with an explicit scope."""

    @provide(scope=Scope.APP)
    def settings(self) -> Settings:
        return get_settings()

    @provide(scope=Scope.APP)
    async def engine(self, settings: Settings) -> AsyncIterable[AsyncEngine]:
        engine = create_engine(settings)
        yield engine
        await engine.dispose()

    @provide(scope=Scope.APP)
    def session_factory(
        self, engine: AsyncEngine
    ) -> async_sessionmaker[AsyncSession]:
        return create_session_factory(engine)

    @provide(scope=Scope.REQUEST)
    async def session(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> AsyncIterable[AsyncSession]:
        # Request-scoped: every repository and the transaction context in one
        # request receive this same session (a shared unit of work). Closed
        # automatically when the request scope exits.
        async with session_factory() as session:
            yield session

    # Stateless services — one instance per process.
    password_hasher = provide(
        BcryptPasswordHasher, provides=PasswordHasher, scope=Scope.APP
    )
    token_service = provide(
        JwtTokenService, provides=TokenService, scope=Scope.APP
    )
    logger = provide(JsonLogger, provides=Logger, scope=Scope.APP)

    # Per-request collaborators — auto-wired from constructor type hints.
    user_repository = provide(
        SqlAlchemyUserRepository, provides=UserRepository, scope=Scope.REQUEST
    )
    transaction_context = provide(
        SqlAlchemyTransactionContext,
        provides=TransactionContext,
        scope=Scope.REQUEST,
    )
    user_use_case = provide(UserUseCase, scope=Scope.REQUEST)
    auth_use_case = provide(AuthUseCase, scope=Scope.REQUEST)
