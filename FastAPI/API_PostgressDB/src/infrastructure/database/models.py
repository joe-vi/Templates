from datetime import datetime

from sqlalchemy import Enum as SQLAlchemyEnum, func
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.enums.greeting_enum import GreetingStatus
from src.infrastructure.database.db import Base

greeting_status_enum = SQLAlchemyEnum(GreetingStatus, name="greeting_status")


class GreetingModel(Base):
    """SQLAlchemy model for greeting."""

    __tablename__ = "greetings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    message: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[GreetingStatus] = mapped_column(greeting_status_enum, nullable=False, default=GreetingStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
