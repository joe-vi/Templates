from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.domain.enums.greeting_enum import GreetingStatus


@dataclass
class Greeting:
    """Domain entity representing a greeting message."""

    id: int | None
    message: str
    status: GreetingStatus = field(default=GreetingStatus.ACTIVE)
    created_at: datetime | None = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
