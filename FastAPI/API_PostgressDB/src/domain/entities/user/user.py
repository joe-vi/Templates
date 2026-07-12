from dataclasses import dataclass, field
from datetime import datetime

from src.domain.enums import user_enum


@dataclass
class User:
    """Aggregate root representing a user of the system."""

    id: int | None
    email: str
    username: str
    hashed_password: str | None = None
    role: user_enum.UserRole = field(default=user_enum.UserRole.USER)
    status: user_enum.UserStatus = field(default=user_enum.UserStatus.ACTIVE)
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate the email and username.

        Raises:
            ValueError: If the email or username is blank, or the email has no
                local part and domain separated by ``@``.
        """
        if not self.username.strip():
            raise ValueError("User invariant violated: username must not be blank")
        if not self.email.strip():
            raise ValueError("User invariant violated: email must not be blank")
        local_part, separator, domain = self.email.partition("@")
        if not (local_part and separator and domain):
            raise ValueError(f"User invariant violated: {self.email!r} is not a valid email address")

    @property
    def is_persisted(self) -> bool:
        """Whether this entity has been stored (id assigned by the database)."""
        return self.id is not None

    @property
    def is_active(self) -> bool:
        """Whether this user may authenticate and act in the system."""
        return self.status is user_enum.UserStatus.ACTIVE

    def activate(self) -> None:
        """Transition the user to ``ACTIVE``, allowing authentication."""
        self.status = user_enum.UserStatus.ACTIVE

    def deactivate(self) -> None:
        """Transition the user to ``INACTIVE``, blocking authentication."""
        self.status = user_enum.UserStatus.INACTIVE
