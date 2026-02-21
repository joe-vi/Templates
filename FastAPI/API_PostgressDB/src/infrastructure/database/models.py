from datetime import datetime

from sqlalchemy import Enum as SQLAlchemyEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.enums.user_enum import UserRole, UserStatus
from src.infrastructure.database.db import Base

user_status_enum = SQLAlchemyEnum(UserStatus, name="user_status")
user_role_enum = SQLAlchemyEnum(UserRole, name="user_role")


class UserModel(Base):
    """SQLAlchemy model for user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(user_role_enum, nullable=False, default=UserRole.USER)
    status: Mapped[UserStatus] = mapped_column(user_status_enum, nullable=False, default=UserStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
