from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateGreetingDTO:
    """DTO for creating a greeting."""

    message: str


@dataclass(frozen=True)
class GreetingDTO:
    """DTO representing a greeting."""

    id: int
    message: str
    created_at: datetime


@dataclass(frozen=True)
class GreetingListDTO:
    """DTO for a list of greetings."""

    greetings: tuple["GreetingDTO", ...]


@dataclass(frozen=True)
class DeleteResultDTO:
    """DTO for deletion result."""

    is_successful: bool
    deleted_id: int | None = None
