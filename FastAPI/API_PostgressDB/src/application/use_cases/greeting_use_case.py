from src.application.converters.greeting_converter import GreetingEntityConverter
from src.application.dtos.greeting_dto import (
    CreateGreetingDTO,
    GreetingDTO,
)
from src.application.use_cases.greeting_use_case_base import GreetingUseCaseBase
from src.domain.enums.operation_results import CreateResult, DeleteResult
from src.domain.repositories.greeting_repository_base import GreetingRepositoryBase


class GreetingUseCase(GreetingUseCaseBase):
    """Use case for greeting operations."""

    def __init__(self, repository: GreetingRepositoryBase):
        """Initialize the greeting use case.

        Args:
            repository: The greeting repository for data persistence operations.
        """
        self._repository = repository

    async def create_greeting(self, create_greeting_dto: CreateGreetingDTO) -> tuple[CreateResult, int | None]:
        greeting = GreetingEntityConverter.to_entity(create_greeting_dto)
        return await self._repository.create(greeting)

    async def get_greeting(self, greeting_id: int) -> GreetingDTO | None:
        greeting = await self._repository.get_by_id(greeting_id)

        if greeting is None:
            return None

        return GreetingEntityConverter.to_dto(greeting)

    async def get_all_greetings(self) -> list[GreetingDTO]:
        greetings = await self._repository.get_all()
        return GreetingEntityConverter.to_dto_list(greetings)

    async def delete_greeting(self, greeting_id: int) -> DeleteResult:
        return await self._repository.delete(greeting_id)
