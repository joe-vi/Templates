from collections.abc import AsyncIterator

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.domain.entities.user.user import User
from src.domain.enums import operation_results
from src.infrastructure.database.base import Base
from src.infrastructure.database.models import user_model
from src.infrastructure.database.sqlalchemy_transaction_context import SqlAlchemyTransactionContext
from src.infrastructure.repositories.user.sqlalchemy_user_repository import SqlAlchemyUserRepository


def _make_user(username: str, email: str) -> User:
    return User(id=None, email=email, username=username, hashed_password="hash")


@pytest.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    # StaticPool keeps one connection so every session sees the same
    # in-memory database.
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await engine.dispose()


async def _count_users(session_factory: async_sessionmaker[AsyncSession]) -> int:
    async with session_factory() as session:
        query_result = await session.execute(select(func.count()).select_from(user_model.UserModel))
        return query_result.scalar_one()


class TestCommit:
    async def test_committed_operations_are_persisted(self, session_factory: async_sessionmaker[AsyncSession]):
        async with session_factory() as session:
            repository = SqlAlchemyUserRepository(session)
            transaction_context = SqlAlchemyTransactionContext(session)

            async with transaction_context.begin() as transaction:
                result, user_id = await repository.create(_make_user("alice", "alice@example.com"))
                assert result == operation_results.CreateResult.SUCCESS
                assert user_id is not None
                await transaction.commit()

        assert await _count_users(session_factory) == 1

    async def test_flush_populates_id_before_commit(self, session_factory: async_sessionmaker[AsyncSession]):
        async with session_factory() as session:
            repository = SqlAlchemyUserRepository(session)
            transaction_context = SqlAlchemyTransactionContext(session)

            async with transaction_context.begin() as transaction:
                result, user_id = await repository.create(_make_user("alice", "alice@example.com"))
                # The id is available inside the block, before commit.
                assert user_id == 1
                await transaction.commit()


class TestRollback:
    async def test_block_exit_without_commit_rolls_back_everything(self, session_factory: async_sessionmaker[AsyncSession]):
        async with session_factory() as session:
            repository = SqlAlchemyUserRepository(session)
            transaction_context = SqlAlchemyTransactionContext(session)

            async with transaction_context.begin():
                result, _ = await repository.create(_make_user("alice", "alice@example.com"))
                assert result == operation_results.CreateResult.SUCCESS
                # Exit without commit — e.g. a later step reported failure.

        assert await _count_users(session_factory) == 0

    async def test_failed_operation_rolls_back_earlier_success(self, session_factory: async_sessionmaker[AsyncSession]):
        """The user-facing guarantee: one failure rolls back the whole unit.

        Models a use case orchestrating two repository calls: the first
        succeeds, the second hits a unique-constraint violation, the use
        case returns without committing — and the first insert must be gone.
        """
        async with session_factory() as session:
            repository = SqlAlchemyUserRepository(session)
            transaction_context = SqlAlchemyTransactionContext(session)

            async with transaction_context.begin() as transaction:
                first_result, _ = await repository.create(_make_user("alice", "alice@example.com"))
                assert first_result == operation_results.CreateResult.SUCCESS

                second_result, _ = await repository.create(_make_user("alice", "duplicate@example.com"))
                assert second_result == operation_results.CreateResult.UNIQUE_CONSTRAINT_ERROR

                if second_result == operation_results.CreateResult.SUCCESS:  # pragma: no cover - documents the all-success gate
                    await transaction.commit()

        assert await _count_users(session_factory) == 0

    async def test_exception_inside_block_rolls_back_and_propagates(self, session_factory: async_sessionmaker[AsyncSession]):
        async with session_factory() as session:
            repository = SqlAlchemyUserRepository(session)
            transaction_context = SqlAlchemyTransactionContext(session)

            with pytest.raises(RuntimeError, match="boom"):
                async with transaction_context.begin():
                    result, _ = await repository.create(_make_user("alice", "alice@example.com"))
                    assert result == operation_results.CreateResult.SUCCESS
                    raise RuntimeError("boom")

        assert await _count_users(session_factory) == 0

    async def test_session_is_usable_after_rolled_back_block(self, session_factory: async_sessionmaker[AsyncSession]):
        """After a failed unit of work, the same session can start a new one."""
        async with session_factory() as session:
            repository = SqlAlchemyUserRepository(session)
            transaction_context = SqlAlchemyTransactionContext(session)

            async with transaction_context.begin():
                await repository.create(_make_user("alice", "alice@example.com"))
                # No commit: rolled back.

            async with transaction_context.begin() as transaction:
                result, _ = await repository.create(_make_user("bob", "bob@example.com"))
                assert result == operation_results.CreateResult.SUCCESS
                await transaction.commit()

        assert await _count_users(session_factory) == 1
