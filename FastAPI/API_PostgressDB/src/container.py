from fastapi_injector import request_scope
from injector import Binder, Injector, Module, singleton

from src.application.services.blob_storage_service_base import BlobStorageServiceBase
from src.application.services.custom_logger_base import CustomLoggerBase
from src.application.use_cases.greeting.greeting_use_case import GreetingUseCase
from src.application.use_cases.greeting.greeting_use_case_base import GreetingUseCaseBase
from src.config.settings import Settings
from src.domain.repositories.greeting.greeting_repository_base import GreetingRepositoryBase
from src.infrastructure.blob_storage.blob_storage_service import BlobStorageService
from src.infrastructure.database.connection_factory import ConnectionFactory
from src.infrastructure.database.connection_factory_base import ConnectionFactoryBase
from src.infrastructure.logging.custom_logger import CustomLogger
from src.infrastructure.repositories.greeting.greeting_repository import GreetingRepository


class AppModule(Module):
    """
    Dependency Injection Module using injector.Module.

    This module uses Binder.bind() to map abstract base classes (interfaces)
    to their concrete implementations, following the Dependency Inversion Principle.
    """

    def configure(self, binder: Binder) -> None:
        binder.bind(
            Settings,
            to=Settings,
            scope=singleton,
        )

        binder.bind(
            ConnectionFactoryBase,
            to=ConnectionFactory,
            scope=singleton,
        )

        binder.bind(
            GreetingRepositoryBase,
            to=GreetingRepository,
        )

        binder.bind(
            CustomLoggerBase,
            to=CustomLogger,
            scope=request_scope,
        )

        binder.bind(
            BlobStorageServiceBase,
            to=BlobStorageService,
            scope=singleton,
        )

        binder.bind(
            GreetingUseCaseBase,
            to=GreetingUseCase,
        )


# Global injector instance
injector = Injector([AppModule()])
