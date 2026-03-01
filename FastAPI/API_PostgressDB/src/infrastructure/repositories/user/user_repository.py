"""SQLAlchemy implementation of the user repository."""

import asyncpg
from injector import inject
from sqlalchemy import delete, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError

from src.domain.entities.user import user as user_module
from src.domain.enums import operation_results, user_enum
from src.domain.repositories.user import user_repository_base
from src.infrastructure.database import connection_factory_base
from src.infrastructure.database.models import user_model


class UserRepository(user_repository_base.UserRepositoryBase):
    """Implementation of user repository using SQLAlchemy."""

    @inject
    def __init__(
        self,
        connection_factory: connection_factory_base.ConnectionFactoryBase,
    ):
        """Initialize the user repository.

        Args:
            connection_factory: The factory for creating database sessions.
        """
        self._connection_factory = connection_factory

    async def create(
        self, user: user_module.User
    ) -> tuple[operation_results.CreateResult, int | None]:
        try:
            async with self._connection_factory.get_session() as session:
                user_model_instance = user_model.UserModel(
                    email=user.email,
                    username=user.username,
                    password_hash=user.hashed_password,
                    role=user.role,
                    status=user.status,
                )
                session.add(user_model_instance)
                await session.flush()
                await session.refresh(user_model_instance)

                return (
                    operation_results.CreateResult.SUCCESS,
                    user_model_instance.id,
                )
        except IntegrityError:
            return (
                operation_results.CreateResult.UNIQUE_CONSTRAINT_ERROR,
                None,
            )
        except DBAPIError as exc:
            # asyncpg wraps driver-level errors in DBAPIError; the root cause
            # must be inspected to distinguish deadlocks from other DB failures.
            if isinstance(
                exc.__cause__, asyncpg.exceptions.DeadlockDetectedError
            ):
                return (operation_results.CreateResult.CONCURRENCY_ERROR, None)
            return (operation_results.CreateResult.FAILURE, None)
        except Exception:
            return (operation_results.CreateResult.FAILURE, None)

    async def get_by_id(self, user_id: int) -> user_module.User | None:
        async with self._connection_factory.get_session(
            is_readonly=True
        ) as session:
            query_result = await session.execute(
                select(user_model.UserModel).where(
                    user_model.UserModel.id == user_id
                )
            )
            user_model_instance = query_result.scalar_one_or_none()

            if user_model_instance is None:
                return None

            return user_module.User(
                id=user_model_instance.id,
                email=user_model_instance.email,
                username=user_model_instance.username,
                hashed_password=user_model_instance.password_hash,
                role=user_model_instance.role,
                status=user_model_instance.status,
                created_at=user_model_instance.created_at,
            )

    async def get_all(self) -> list[user_module.User]:
        async with self._connection_factory.get_session(
            is_readonly=True
        ) as session:
            query_result = await session.execute(select(user_model.UserModel))
            user_model_instances = query_result.scalars().all()

            return [
                user_module.User(
                    id=instance.id,
                    email=instance.email,
                    username=instance.username,
                    hashed_password=instance.password_hash,
                    role=instance.role,
                    status=instance.status,
                    created_at=instance.created_at,
                )
                for instance in user_model_instances
            ]

    async def get_by_username(self, username: str) -> user_module.User | None:
        async with self._connection_factory.get_session(
            is_readonly=True
        ) as session:
            query_result = await session.execute(
                select(user_model.UserModel).where(
                    user_model.UserModel.username == username
                )
            )
            user_model_instance = query_result.scalar_one_or_none()

            if user_model_instance is None:
                return None

            return user_module.User(
                id=user_model_instance.id,
                email=user_model_instance.email,
                username=user_model_instance.username,
                hashed_password=user_model_instance.password_hash,
                role=user_model_instance.role,
                status=user_model_instance.status,
                created_at=user_model_instance.created_at,
            )

    async def update_role(
        self, user_id: int, role: user_enum.UserRole
    ) -> operation_results.UpdateResult:
        try:
            async with self._connection_factory.get_session() as session:
                update_result = await session.execute(
                    update(user_model.UserModel)
                    .where(user_model.UserModel.id == user_id)
                    .values(role=role)
                )
                return (
                    operation_results.UpdateResult.SUCCESS
                    if update_result.rowcount > 0
                    else operation_results.UpdateResult.NOT_FOUND
                )
        except DBAPIError as exc:
            # See create() for why __cause__ is inspected here.
            if isinstance(
                exc.__cause__, asyncpg.exceptions.DeadlockDetectedError
            ):
                return operation_results.UpdateResult.CONCURRENCY_ERROR
            return operation_results.UpdateResult.FAILURE
        except Exception:
            return operation_results.UpdateResult.FAILURE

    async def delete(self, user_id: int) -> operation_results.DeleteResult:
        try:
            async with self._connection_factory.get_session() as session:
                delete_result = await session.execute(
                    delete(user_model.UserModel).where(
                        user_model.UserModel.id == user_id
                    )
                )
                return (
                    operation_results.DeleteResult.SUCCESS
                    if delete_result.rowcount > 0
                    else operation_results.DeleteResult.NOT_FOUND
                )
        except DBAPIError as exc:
            # See create() for why __cause__ is inspected here.
            if isinstance(
                exc.__cause__, asyncpg.exceptions.DeadlockDetectedError
            ):
                return operation_results.DeleteResult.CONCURRENCY_ERROR
            return operation_results.DeleteResult.FAILURE
        except Exception:
            return operation_results.DeleteResult.FAILURE
