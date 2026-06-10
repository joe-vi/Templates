"""Composition root: FastAPI dependency providers wiring ports to adapters.

These functions replace a separate IoC container. FastAPI's own dependency
system resolves the graph, caches per request, and supports overrides in tests
via ``app.dependency_overrides``.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.database import get_session
from src.application.services.logger import Logger
from src.application.services.password_hasher import PasswordHasher
from src.application.services.token_service import TokenService
from src.application.use_cases.auth.auth_use_case import AuthUseCase
from src.application.use_cases.user.user_use_case import UserUseCase
from src.config.settings import get_settings
from src.domain.repositories.user.user_repository import UserRepository
from src.infrastructure.auth.bcrypt_password_hasher import BcryptPasswordHasher
from src.infrastructure.auth.jwt_token_service import JwtTokenService
from src.infrastructure.logging.json_logger import JsonLogger
from src.infrastructure.repositories.user.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)


@lru_cache
def get_password_hasher() -> PasswordHasher:
    """Return the process-wide password hasher (stateless singleton)."""
    return BcryptPasswordHasher()


@lru_cache
def get_token_service() -> TokenService:
    """Return the process-wide token service (stateless singleton)."""
    return JwtTokenService(get_settings())


@lru_cache
def get_logger() -> Logger:
    """Return the process-wide structured logger (singleton)."""
    return JsonLogger(get_settings())


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserRepository:
    """Build a user repository bound to the request-scoped session."""
    return SqlAlchemyUserRepository(session)


def get_user_use_case(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
) -> UserUseCase:
    """Build the user use case for the current request."""
    return UserUseCase(repository=repository, password_hasher=password_hasher)


def get_auth_use_case(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    logger: Annotated[Logger, Depends(get_logger)],
) -> AuthUseCase:
    """Build the authentication use case for the current request."""
    return AuthUseCase(
        user_repository=repository,
        password_hasher=password_hasher,
        token_service=token_service,
        logger=logger,
    )
