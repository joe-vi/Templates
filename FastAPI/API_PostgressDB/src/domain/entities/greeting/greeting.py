from dataclasses import dataclass, field
from datetime import datetime

from src.domain.enums.greeting_enum import GreetingStatus


@dataclass
class Greeting:
    """Domain entity representing a greeting message."""

    id: int | None
    message: str
    status: GreetingStatus = field(default=GreetingStatus.ACTIVE)
    created_at: datetime | None = None
