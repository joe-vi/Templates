from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from src.infrastructure.database.connection_factory import Base


class GreetingModel(Base):
    """SQLAlchemy model for greeting."""

    __tablename__ = "greetings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
