from typing import Any, cast

from injector import inject
from sqlalchemy import CursorResult, delete, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError

from src.domain.entities.user.user import User
from src.domain.enums import operation_results, user_enum
from src.domain.repositories.user.user_repository import UserRepository
from src.infrastructure.database.connection_factory import ConnectionFactory
from src.infrastructure.database.errors import is_deadlock
from src.infrastructure.database.models import user_model


def _to_entity(model: user_model.UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        username=model.username,
        hashed_password=model.password_hash,
        role=model.role,
        status=model.status,
        created_at=model.created_at,
    )


class SqlAlchemyUserRepository(UserRepository):
    """``UserRepository`` adapter backed by SQLAlchemy and PostgreSQL."""

    @inject
    def __init__(self, connections: ConnectionFactory) -> None:
        self._connections = connections

    async def create(self, user: User) -> tuple[operation_results.CreateResult, int | None]:
        model = user_model.UserModel(
            email=user.email, username=user.username, password_hash=user.hashed_password, role=user.role, status=user.status
        )
        try:
            async with self._connections.write() as session:
                session.add(model)
                # Flush executes the INSERT (RETURNING populates id and server
                # defaults) without ending the transaction, so this call can
                # participate in a multi-operation unit of work.
                await session.flush()
                return (operation_results.CreateResult.SUCCESS, model.id)
        except IntegrityError:
            return (operation_results.CreateResult.UNIQUE_CONSTRAINT_ERROR, None)
        except DBAPIError as exc:
            return (operation_results.CreateResult.CONCURRENCY_ERROR if is_deadlock(exc) else operation_results.CreateResult.FAILURE, None)
        except Exception:
            return (operation_results.CreateResult.FAILURE, None)

    async def get_by_id(self, user_id: int) -> User | None:
        async with self._connections.read() as session:
            query_result = await session.execute(select(user_model.UserModel).where(user_model.UserModel.id == user_id))
            model = query_result.scalar_one_or_none()
            return _to_entity(model) if model is not None else None

    async def get_all(self) -> list[User]:
        async with self._connections.read() as session:
            query_result = await session.execute(select(user_model.UserModel))
            return [_to_entity(model) for model in query_result.scalars().all()]

    async def get_by_username(self, username: str) -> User | None:
        async with self._connections.read() as session:
            query_result = await session.execute(select(user_model.UserModel).where(user_model.UserModel.username == username))
            model = query_result.scalar_one_or_none()
            return _to_entity(model) if model is not None else None

    async def update_role(self, user_id: int, role: user_enum.UserRole) -> operation_results.UpdateResult:
        try:
            async with self._connections.write() as session:
                # execute() returns CursorResult for UPDATE/DELETE at runtime;
                # the static type is Result, which lacks rowcount.
                update_result = cast(
                    "CursorResult[Any]",
                    await session.execute(update(user_model.UserModel).where(user_model.UserModel.id == user_id).values(role=role)),
                )
                return operation_results.UpdateResult.SUCCESS if update_result.rowcount > 0 else operation_results.UpdateResult.NOT_FOUND
        except DBAPIError as exc:
            return operation_results.UpdateResult.CONCURRENCY_ERROR if is_deadlock(exc) else operation_results.UpdateResult.FAILURE
        except Exception:
            return operation_results.UpdateResult.FAILURE

    async def delete(self, user_id: int) -> operation_results.DeleteResult:
        try:
            async with self._connections.write() as session:
                delete_result = cast(
                    "CursorResult[Any]", await session.execute(delete(user_model.UserModel).where(user_model.UserModel.id == user_id))
                )
                return operation_results.DeleteResult.SUCCESS if delete_result.rowcount > 0 else operation_results.DeleteResult.NOT_FOUND
        except DBAPIError as exc:
            return operation_results.DeleteResult.CONCURRENCY_ERROR if is_deadlock(exc) else operation_results.DeleteResult.FAILURE
        except Exception:
            return operation_results.DeleteResult.FAILURE
