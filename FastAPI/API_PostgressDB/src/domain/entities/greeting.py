from dataclasses import dataclass
from datetime import datetime


@dataclass
class Greeting:
    """Domain entity representing a greeting message."""

    id: int | None
    message: str
    created_at: datetime | None = None

    def __post_init__(self):
        """Set the created_at timestamp to the current UTC time if not provided."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
