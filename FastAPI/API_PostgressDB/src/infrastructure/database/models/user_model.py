"""SQLAlchemy ORM model for the users table."""

from datetime import datetime

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.enums import user_enum
from src.infrastructure.database import base as database_base

user_status_enum = SQLAlchemyEnum(user_enum.UserStatus, name="user_status")
user_role_enum = SQLAlchemyEnum(user_enum.UserRole, name="user_role")


class UserModel(database_base.Base):
    """SQLAlchemy model for user."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    role: Mapped[user_enum.UserRole] = mapped_column(
        user_role_enum, nullable=False, default=user_enum.UserRole.USER
    )
    status: Mapped[user_enum.UserStatus] = mapped_column(
        user_status_enum, nullable=False, default=user_enum.UserStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
