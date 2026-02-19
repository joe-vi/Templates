from src.application.converters.greeting_converter import GreetingEntityConverter
from src.application.dtos.greeting_dto import (
    CreateGreetingDTO,
    DeleteResultDTO,
    GreetingDTO,
    GreetingListDTO,
)
from src.application.use_cases.greeting_use_case_base import GreetingUseCaseBase
from src.domain.repositories.greeting_repository_base import GreetingRepositoryBase


class GreetingUseCase(GreetingUseCaseBase):
    """Use case for greeting operations."""

    def __init__(self, repository: GreetingRepositoryBase):
        """Initialize the greeting use case.

        Args:
            repository: The greeting repository for data persistence operations.
        """
        self._repository = repository

    async def create_greeting(self, create_greeting_dto: CreateGreetingDTO) -> GreetingDTO:
        greeting = GreetingEntityConverter.to_entity(create_greeting_dto)
        created_greeting = await self._repository.create(greeting)
        return GreetingEntityConverter.to_dto(created_greeting)

    async def get_greeting(self, greeting_id: int) -> GreetingDTO | None:
        greeting = await self._repository.get_by_id(greeting_id)

        if greeting is None:
            return None

        return GreetingEntityConverter.to_dto(greeting)

    async def get_all_greetings(self) -> GreetingListDTO:
        greetings = await self._repository.get_all()
        return GreetingEntityConverter.to_dto_list(greetings)

    async def delete_greeting(self, greeting_id: int) -> DeleteResultDTO:
        is_deleted = await self._repository.delete(greeting_id)
        return DeleteResultDTO(
            is_successful=is_deleted,
            deleted_id=greeting_id if is_deleted else None,
        )
