import asyncpg
from injector import inject
from sqlalchemy import delete, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError

from src.domain.entities.user.user import User
from src.domain.enums.operation_results import CreateResult, DeleteResult, UpdateResult
from src.domain.enums.user_enum import UserRole
from src.domain.repositories.user.user_repository_base import UserRepositoryBase
from src.infrastructure.database.connection_factory_base import ConnectionFactoryBase
from src.infrastructure.database.models import UserModel


class UserRepository(UserRepositoryBase):
    """Implementation of user repository using SQLAlchemy."""

    @inject
    def __init__(self, connection_factory: ConnectionFactoryBase):
        """Initialize the user repository.

        Args:
            connection_factory: The factory for creating database sessions.
        """
        self._connection_factory = connection_factory

    async def create(self, user: User) -> tuple[CreateResult, int | None]:
        try:
            async with self._connection_factory.get_session() as session:
                user_model = UserModel(
                    email=user.email,
                    username=user.username,
                    password_hash=user.hashed_password,
                    role=user.role,
                    status=user.status,
                )
                session.add(user_model)
                await session.flush()
                await session.refresh(user_model)

                return (CreateResult.SUCCESS, user_model.id)
        except IntegrityError:
            return (CreateResult.UNIQUE_CONSTRAINT_ERROR, None)
        except DBAPIError as exc:
            if isinstance(exc.__cause__, asyncpg.exceptions.DeadlockDetectedError):
                return (CreateResult.CONCURRENCY_ERROR, None)
            return (CreateResult.FAILURE, None)
        except Exception:
            return (CreateResult.FAILURE, None)

    async def get_by_id(self, user_id: int) -> User | None:
        async with self._connection_factory.get_session(is_readonly=True) as session:
            query_result = await session.execute(select(UserModel).where(UserModel.id == user_id))
            user_model = query_result.scalar_one_or_none()

            if user_model is None:
                return None

            return User(
                id=user_model.id,
                email=user_model.email,
                username=user_model.username,
                hashed_password=user_model.password_hash,
                role=user_model.role,
                status=user_model.status,
                created_at=user_model.created_at,
            )

    async def get_all(self) -> list[User]:
        async with self._connection_factory.get_session(is_readonly=True) as session:
            query_result = await session.execute(select(UserModel))
            user_models = query_result.scalars().all()

            return [
                User(
                    id=user_model.id,
                    email=user_model.email,
                    username=user_model.username,
                    hashed_password=user_model.password_hash,
                    role=user_model.role,
                    status=user_model.status,
                    created_at=user_model.created_at,
                )
                for user_model in user_models
            ]

    async def get_by_username(self, username: str) -> User | None:
        async with self._connection_factory.get_session(is_readonly=True) as session:
            query_result = await session.execute(select(UserModel).where(UserModel.username == username))
            user_model = query_result.scalar_one_or_none()

            if user_model is None:
                return None

            return User(
                id=user_model.id,
                email=user_model.email,
                username=user_model.username,
                hashed_password=user_model.password_hash,
                role=user_model.role,
                status=user_model.status,
                created_at=user_model.created_at,
            )

    async def update_role(self, user_id: int, role: UserRole) -> UpdateResult:
        try:
            async with self._connection_factory.get_session() as session:
                update_result = await session.execute(update(UserModel).where(UserModel.id == user_id).values(role=role))
                return UpdateResult.SUCCESS if update_result.rowcount > 0 else UpdateResult.NOT_FOUND
        except DBAPIError as exc:
            if isinstance(exc.__cause__, asyncpg.exceptions.DeadlockDetectedError):
                return UpdateResult.CONCURRENCY_ERROR
            return UpdateResult.FAILURE
        except Exception:
            return UpdateResult.FAILURE

    async def delete(self, user_id: int) -> DeleteResult:
        try:
            async with self._connection_factory.get_session() as session:
                delete_result = await session.execute(delete(UserModel).where(UserModel.id == user_id))
                return DeleteResult.SUCCESS if delete_result.rowcount > 0 else DeleteResult.NOT_FOUND
        except DBAPIError as exc:
            if isinstance(exc.__cause__, asyncpg.exceptions.DeadlockDetectedError):
                return DeleteResult.CONCURRENCY_ERROR
            return DeleteResult.FAILURE
        except Exception:
            return DeleteResult.FAILURE
