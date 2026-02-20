import asyncpg
from sqlalchemy import delete, select
from sqlalchemy.exc import DBAPIError, IntegrityError

from src.domain.entities.greeting.greeting import Greeting
from src.domain.enums.operation_results import CreateResult, DeleteResult
from src.domain.repositories.greeting.greeting_repository_base import GreetingRepositoryBase
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

    async def create(self, greeting: Greeting) -> tuple[CreateResult, int | None]:
        try:
            async with self._connection_factory.get_session() as session:
                greeting_model = GreetingModel(
                    message=greeting.message,
                    status=greeting.status,
                )
                session.add(greeting_model)
                await session.flush()
                await session.refresh(greeting_model)

                return (CreateResult.SUCCESS, greeting_model.id)
        except IntegrityError:
            return (CreateResult.UNIQUE_CONSTRAINT_ERROR, None)
        except DBAPIError as exc:
            if isinstance(exc.__cause__, asyncpg.exceptions.DeadlockDetectedError):
                return (CreateResult.CONCURRENCY_ERROR, None)
            return (CreateResult.FAILURE, None)
        except Exception:
            return (CreateResult.FAILURE, None)

    async def get_by_id(self, greeting_id: int) -> Greeting | None:
        async with self._connection_factory.get_session() as session:
            query_result = await session.execute(select(GreetingModel).where(GreetingModel.id == greeting_id))
            greeting_model = query_result.scalar_one_or_none()

            if greeting_model is None:
                return None

            return Greeting(
                id=greeting_model.id,
                message=greeting_model.message,
                status=greeting_model.status,
                created_at=greeting_model.created_at,
            )

    async def get_all(self) -> list[Greeting]:
        async with self._connection_factory.get_session() as session:
            query_result = await session.execute(select(GreetingModel))
            greeting_models = query_result.scalars().all()

            return [
                Greeting(
                    id=greeting_model.id,
                    message=greeting_model.message,
                    status=greeting_model.status,
                    created_at=greeting_model.created_at,
                )
                for greeting_model in greeting_models
            ]

    async def delete(self, greeting_id: int) -> DeleteResult:
        try:
            async with self._connection_factory.get_session() as session:
                delete_result = await session.execute(delete(GreetingModel).where(GreetingModel.id == greeting_id))
                return DeleteResult.SUCCESS if delete_result.rowcount > 0 else DeleteResult.NOT_FOUND
        except DBAPIError as exc:
            if isinstance(exc.__cause__, asyncpg.exceptions.DeadlockDetectedError):
                return DeleteResult.CONCURRENCY_ERROR
            return DeleteResult.FAILURE
        except Exception:
            return DeleteResult.FAILURE
