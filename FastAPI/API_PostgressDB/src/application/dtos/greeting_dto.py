from dataclasses import dataclass
from datetime import datetime

from src.domain.enums.greeting_enum import GreetingStatus


@dataclass(frozen=True)
class CreateGreetingDTO:
    """DTO for creating a greeting."""

    message: str
    status: GreetingStatus = GreetingStatus.ACTIVE


@dataclass(frozen=True)
class GreetingDTO:
    """DTO representing a greeting."""

    id: int
    message: str
    status: GreetingStatus
    created_at: datetime


