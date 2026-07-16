from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.entities.user import user as user_module
from src.domain.enums import user_enum
from src.domain.repositories.user.user_repository import UserRepository
from src.ports.password_hasher import PasswordHasher


class FakeTransaction:
    """In-memory transaction handle recording whether commit was called."""

    def __init__(self) -> None:
        self.is_committed = False

    async def commit(self) -> None:
        self.is_committed = True


class FakeTransactionContext:
    """In-memory TransactionContext satisfying the port structurally."""

    def __init__(self) -> None:
        self.transaction = FakeTransaction()
        self.is_rolled_back = False

    @asynccontextmanager
    async def begin(self) -> AsyncGenerator[FakeTransaction]:
        try:
            yield self.transaction
        finally:
            if not self.transaction.is_committed:
                self.is_rolled_back = True


@pytest.fixture
def make_user() -> Callable[..., user_module.User]:
    def _make_user(user_id: int = 1) -> user_module.User:
        return user_module.User(
            id=user_id,
            email="alice@example.com",
            username="alice",
            role=user_enum.UserRole.USER,
            status=user_enum.UserStatus.ACTIVE,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )

    return _make_user


@pytest.fixture
def mock_repository() -> UserRepository:
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def mock_password_hasher() -> PasswordHasher:
    hasher = MagicMock(spec=PasswordHasher)
    hasher.hash.return_value = "hashed_password"
    return hasher


@pytest.fixture
def fake_transaction_context() -> FakeTransactionContext:
    return FakeTransactionContext()
