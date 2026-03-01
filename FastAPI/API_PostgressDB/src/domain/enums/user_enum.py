"""User-related domain enumerations."""

from enum import StrEnum


class UserStatus(StrEnum):
    """Represents the lifecycle status of a user."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class UserRole(StrEnum):
    """Represents the role of a user."""

    ADMIN = "admin"
    USER = "user"
