from sqlalchemy import delete, select

from src.domain.entities.greeting import Greeting
from src.domain.repositories.greeting_repository_base import GreetingRepositoryBase
from src.infrastructure.database.connection_factory_base import ConnectionFactoryBase
from src.infrastructure.database.models import GreetingModel


class GreetingRepository(GreetingRepositoryBase):
    """Implementation of greeting repository using SQLAlchemy."""

    def __init__(self, connection_factory: ConnectionFactoryBase):
        """Initialize the greeting repository.

        Args:
            connection_factory: The factory for creating database sessions.
        """
        self._connection_factory = connection_factory

    async def create(self, greeting: Greeting) -> Greeting:
        """Persist a new greeting entity to the database.

        Args:
            greeting: The greeting entity to persist.

        Returns:
            The persisted Greeting entity with generated id and timestamps.
        """
        async with self._connection_factory.get_session() as session:
            greeting_model = GreetingModel(
                message=greeting.message,
                created_at=greeting.created_at,
            )
            session.add(greeting_model)
            await session.flush()
            await session.refresh(greeting_model)

            return Greeting(
                id=greeting_model.id,
                message=greeting_model.message,
                created_at=greeting_model.created_at,
            )

    async def get_by_id(self, greeting_id: int) -> Greeting | None:
        """Retrieve a greeting entity by its unique identifier.

        Args:
            greeting_id: The unique identifier of the greeting to retrieve.

        Returns:
            The Greeting entity if found, None otherwise.
        """
        async with self._connection_factory.get_session() as session:
            query_result = await session.execute(select(GreetingModel).where(GreetingModel.id == greeting_id))
            greeting_model = query_result.scalar_one_or_none()

            if greeting_model is None:
                return None

            return Greeting(
                id=greeting_model.id,
                message=greeting_model.message,
                created_at=greeting_model.created_at,
            )

    async def get_all(self) -> list[Greeting]:
        """Retrieve all greeting entities from the database.

        Returns:
            A list of all Greeting entities.
        """
        async with self._connection_factory.get_session() as session:
            query_result = await session.execute(select(GreetingModel))
            greeting_models = query_result.scalars().all()

            return [
                Greeting(
                    id=greeting_model.id,
                    message=greeting_model.message,
                    created_at=greeting_model.created_at,
                )
                for greeting_model in greeting_models
            ]

    async def delete(self, greeting_id: int) -> bool:
        """Delete a greeting entity by its unique identifier.

        Args:
            greeting_id: The unique identifier of the greeting to delete.

        Returns:
            True if the greeting was deleted, False if it was not found.
        """
        async with self._connection_factory.get_session() as session:
            delete_result = await session.execute(delete(GreetingModel).where(GreetingModel.id == greeting_id))
            return delete_result.rowcount > 0
