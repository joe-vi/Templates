"""Dependency injection container and module configuration."""

from fastapi_injector import request_scope
from injector import Binder, Injector, Module, singleton

from src.application.services import (
    custom_logger_base,
    password_hasher_base,
    token_service_base,
    transaction_manager_base,
    user_context_base,
)
from src.application.use_cases.auth import auth_use_case, auth_use_case_base
from src.application.use_cases.user import user_use_case, user_use_case_base
from src.config import settings as settings_module
from src.domain.repositories.user import user_repository_base
from src.infrastructure.auth import password_hasher, token_service, user_context
from src.infrastructure.database import (
    connection_factory,
    connection_factory_base,
    transaction_manager,
)
from src.infrastructure.logging import custom_logger
from src.infrastructure.repositories.user import user_repository


class AppModule(Module):
    """Dependency Injection module mapping interfaces to implementations.

    Uses Binder.bind() to map abstract base classes (interfaces) to their
    concrete implementations, following the Dependency Inversion Principle.
    """

    def configure(self, binder: Binder) -> None:
        """Bind interface–implementation pairs and assign DI scopes."""
        # Singletons
        binder.bind(
            settings_module.Settings,
            to=settings_module.Settings,
            scope=singleton,
        )
        binder.bind(
            connection_factory_base.ConnectionFactoryBase,
            to=connection_factory.ConnectionFactory,
            scope=singleton,
        )
        binder.bind(
            password_hasher_base.PasswordHasherBase,
            to=password_hasher.PasswordHasher,
            scope=singleton,
        )
        binder.bind(
            token_service_base.TokenServiceBase,
            to=token_service.TokenService,
            scope=singleton,
        )

        # Request-scoped services
        binder.bind(
            custom_logger_base.CustomLoggerBase,
            to=custom_logger.CustomLogger,
            scope=request_scope,
        )
        binder.bind(
            user_context_base.UserContextBase,
            to=user_context.UserContext,
            scope=request_scope,
        )

        # Repositories
        binder.bind(
            transaction_manager_base.TransactionManagerBase,
            to=transaction_manager.TransactionManager,
        )
        binder.bind(
            user_repository_base.UserRepositoryBase,
            to=user_repository.UserRepository,
        )

        # Use cases
        binder.bind(
            user_use_case_base.UserUseCaseBase, to=user_use_case.UserUseCase
        )
        binder.bind(
            auth_use_case_base.AuthUseCaseBase, to=auth_use_case.AuthUseCase
        )


injector = Injector([AppModule()])
