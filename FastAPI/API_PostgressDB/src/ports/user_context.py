from typing import Protocol

from src.domain.enums import user_enum


class UserContext(Protocol):
    """Port holding the authenticated caller's identity for one request."""

    @property
    def user_id(self) -> int | None:
        """The authenticated user's id, or ``None`` on an unauthenticated request."""
        ...

    @property
    def role(self) -> user_enum.UserRole | None:
        """The authenticated user's role, or ``None`` on an unauthenticated request."""
        ...

    def populate(self, user_id: int, role: user_enum.UserRole) -> None:
        """Store the caller's identity; called exactly once per request.

        Args:
            user_id: The authenticated user's unique identifier.
            role: The authenticated user's role.

        Raises:
            RuntimeError: If the context was already populated.
        """
        ...
