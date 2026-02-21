from fastapi_injector import request_scope
from injector import Binder, Injector, Module, singleton

from src.application.services.custom_logger_base import CustomLoggerBase
from src.application.services.password_hasher_base import PasswordHasherBase
from src.application.services.token_service_base import TokenServiceBase
from src.application.services.transaction_manager_base import TransactionManagerBase
from src.application.services.user_context_base import UserContextBase
from src.application.use_cases.auth.auth_use_case import AuthUseCase
from src.application.use_cases.auth.auth_use_case_base import AuthUseCaseBase
from src.application.use_cases.user.user_use_case import UserUseCase
from src.application.use_cases.user.user_use_case_base import UserUseCaseBase
from src.config.settings import Settings
from src.domain.repositories.user.user_repository_base import UserRepositoryBase
from src.infrastructure.auth.password_hasher import PasswordHasher
from src.infrastructure.auth.token_service import TokenService
from src.infrastructure.auth.user_context import UserContext
from src.infrastructure.database.connection_factory import ConnectionFactory
from src.infrastructure.database.connection_factory_base import ConnectionFactoryBase
from src.infrastructure.database.transaction_manager import TransactionManager
from src.infrastructure.logging.custom_logger import CustomLogger
from src.infrastructure.repositories.user.user_repository import UserRepository


class AppModule(Module):
    """
    Dependency Injection Module using injector.Module.

    This module uses Binder.bind() to map abstract base classes (interfaces)
    to their concrete implementations, following the Dependency Inversion Principle.
    """

    def configure(self, binder: Binder) -> None:
        # Singletons
        binder.bind(Settings, to=Settings, scope=singleton)
        binder.bind(ConnectionFactoryBase, to=ConnectionFactory, scope=singleton)
        binder.bind(PasswordHasherBase, to=PasswordHasher, scope=singleton)
        binder.bind(TokenServiceBase, to=TokenService, scope=singleton)

        # Request-scoped services
        binder.bind(CustomLoggerBase, to=CustomLogger, scope=request_scope)
        binder.bind(UserContextBase, to=UserContext, scope=request_scope)

        # Repositories
        binder.bind(TransactionManagerBase, to=TransactionManager)
        binder.bind(UserRepositoryBase, to=UserRepository)

        # Use cases
        binder.bind(UserUseCaseBase, to=UserUseCase)
        binder.bind(AuthUseCaseBase, to=AuthUseCase)


injector = Injector([AppModule()])
