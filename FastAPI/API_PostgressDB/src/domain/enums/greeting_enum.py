from enum import StrEnum


class GreetingStatus(StrEnum):
    """Represents the lifecycle status of a greeting."""

    ACTIVE = "active"
    ARCHIVED = "archived"
