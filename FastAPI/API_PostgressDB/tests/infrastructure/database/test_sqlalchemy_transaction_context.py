from collections.abc import AsyncIterator

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.domain.entities.user.user import User
from src.domain.enums import operation_results
from src.infrastructure.database.base import Base
from src.infrastructure.database.models import user_model
from src.infrastructure.database.sqlalchemy_connection_factory import SqlAlchemyConnectionFactory
from src.infrastructure.database.sqlalchemy_transaction_context import SqlAlchemyTransactionContext
from src.infrastructure.repositories.user.sqlalchemy_user_repository import SqlAlchemyUserRepository


def _make_user(username: str, email: str) -> User:
    return User(id=None, email=email, username=username, hashed_password="hash")


def _build(session_factory: async_sessionmaker[AsyncSession]) -> tuple[SqlAlchemyTransactionContext, SqlAlchemyUserRepository]:
    transaction_context = SqlAlchemyTransactionContext(session_factory)
    repository = SqlAlchemyUserRepository(SqlAlchemyConnectionFactory(session_factory, transaction_context))
    return transaction_context, repository


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


class TestSingleWrite:
    async def test_single_write_self_commits(self, session_factory: async_sessionmaker[AsyncSession]):
        _, repository = _build(session_factory)

        result, user_id = await repository.create(_make_user("alice", "alice@example.com"))

        assert result == operation_results.CreateResult.SUCCESS
        assert user_id is not None
        assert await _count_users(session_factory) == 1

    async def test_flush_populates_id_inside_the_unit(self, session_factory: async_sessionmaker[AsyncSession]):
        transaction_context, repository = _build(session_factory)

        async with transaction_context.begin():
            result, user_id = await repository.create(_make_user("alice", "alice@example.com"))
            # The id is available inside the block, before the unit commits.
            assert user_id == 1


class TestMultiWriteAtomicity:
    async def test_multiple_writes_commit_atomically(self, session_factory: async_sessionmaker[AsyncSession]):
        transaction_context, repository = _build(session_factory)

        async with transaction_context.begin():
            await repository.create(_make_user("alice", "alice@example.com"))
            await repository.create(_make_user("bob", "bob@example.com"))
            # Clean exit commits both writes together.

        assert await _count_users(session_factory) == 2

    async def test_explicit_rollback_discards_the_unit(self, session_factory: async_sessionmaker[AsyncSession]):
        transaction_context, repository = _build(session_factory)

        async with transaction_context.begin() as transaction:
            result, _ = await repository.create(_make_user("alice", "alice@example.com"))
            assert result == operation_results.CreateResult.SUCCESS
            # A benign failure downstream would abort the unit explicitly.
            await transaction.rollback()

        assert await _count_users(session_factory) == 0

    async def test_exception_inside_block_rolls_back_and_propagates(self, session_factory: async_sessionmaker[AsyncSession]):
        transaction_context, repository = _build(session_factory)

        with pytest.raises(RuntimeError, match="boom"):
            async with transaction_context.begin():
                result, _ = await repository.create(_make_user("alice", "alice@example.com"))
                assert result == operation_results.CreateResult.SUCCESS
                raise RuntimeError("boom")

        assert await _count_users(session_factory) == 0

    async def test_new_unit_is_usable_after_a_rolled_back_one(self, session_factory: async_sessionmaker[AsyncSession]):
        transaction_context, repository = _build(session_factory)

        async with transaction_context.begin() as transaction:
            await repository.create(_make_user("alice", "alice@example.com"))
            await transaction.rollback()

        async with transaction_context.begin():
            result, _ = await repository.create(_make_user("bob", "bob@example.com"))
            assert result == operation_results.CreateResult.SUCCESS

        assert await _count_users(session_factory) == 1


class TestPoisonedUnit:
    async def test_db_failure_rolls_back_whole_unit_and_fails_following_writes(self, session_factory: async_sessionmaker[AsyncSession]):
        """A DB error in a nested write rolls the whole unit back and every following write in it fails fast."""
        transaction_context, repository = _build(session_factory)

        async with transaction_context.begin():
            first_result, _ = await repository.create(_make_user("alice", "alice@example.com"))
            assert first_result == operation_results.CreateResult.SUCCESS

            # Duplicate username: the IntegrityError is caught by the repository, but the nested
            # write scope has already rolled the whole unit back.
            second_result, _ = await repository.create(_make_user("alice", "second@example.com"))
            assert second_result == operation_results.CreateResult.UNIQUE_CONSTRAINT_ERROR

            # The unit is dead: a following write fails fast rather than running on a fresh transaction.
            third_result, _ = await repository.create(_make_user("carol", "carol@example.com"))
            assert third_result == operation_results.CreateResult.FAILURE

        assert await _count_users(session_factory) == 0


class TestReads:
    async def test_read_sees_committed_writes(self, session_factory: async_sessionmaker[AsyncSession]):
        _, repository = _build(session_factory)

        await repository.create(_make_user("alice", "alice@example.com"))

        loaded = await repository.get_by_username("alice")
        assert loaded is not None
        assert loaded.email == "alice@example.com"
