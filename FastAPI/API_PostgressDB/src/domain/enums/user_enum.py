from enum import StrEnum


class UserStatus(StrEnum):
    """Lifecycle status of a user; only ``ACTIVE`` users may authenticate."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class UserRole(StrEnum):
    """Authorization role of a user."""

    ADMIN = "admin"
    USER = "user"
