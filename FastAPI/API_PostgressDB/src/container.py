from injector import Binder, Injector, Module, singleton

from src.application.use_cases.greeting_use_case import GreetingUseCase
from src.application.use_cases.greeting_use_case_base import GreetingUseCaseBase
from src.config.settings import Settings
from src.domain.repositories.greeting_repository_base import GreetingRepositoryBase
from src.infrastructure.database.connection_factory import ConnectionFactory
from src.infrastructure.database.connection_factory_base import ConnectionFactoryBase
from src.infrastructure.repositories.greeting_repository import GreetingRepository


class AppModule(Module):
    """
    Dependency Injection Module using injector.Module.

    This module uses Binder.bind() to map abstract base classes (interfaces)
    to their concrete implementations, following the Dependency Inversion Principle.
    """

    def configure(self, binder: Binder) -> None:
        """Configure dependency bindings mapping interfaces to implementations.

        Args:
            binder: The injector binder used to register interface-to-implementation mappings.
        """

        # Bind Settings as singleton
        # Singleton scope ensures configuration is loaded once and shared
        binder.bind(
            Settings,  # Concrete class
            to=Settings,  # Implementation
            scope=singleton,  # Singleton scope
        )

        # Bind ConnectionFactory interface to implementation as singleton
        # Singleton scope ensures one instance manages the connection pool
        binder.bind(
            ConnectionFactoryBase,  # Interface (ABC)
            to=ConnectionFactory,  # Implementation
            scope=singleton,  # Singleton scope
        )

        # Bind Repository interfaces to implementations (request scope by default)
        binder.bind(
            GreetingRepositoryBase,  # Interface (ABC)
            to=GreetingRepository,  # Implementation
        )

        # Bind Use Case interfaces to implementations (request scope by default)
        binder.bind(
            GreetingUseCaseBase,  # Interface (ABC)
            to=GreetingUseCase,  # Implementation
        )


# Global injector instance
injector = Injector([AppModule()])
