"""Request-scoped user context port (structural interface)."""

from typing import Protocol

from src.domain.enums import user_enum


class UserContext(Protocol):
    """Port holding the authenticated caller's identity for one request.

    Populated exactly once per request by the JWT guard after the Bearer
    token is validated. Inject into any use case or service that needs the
    caller's identity — auditing, ownership checks, role/permission checks —
    instead of threading claims through every method signature.

    Only valid on routes protected by the guard: reading an unpopulated
    context raises RuntimeError.
    """

    @property
    def is_populated(self) -> bool:
        """Whether the context has been populated for this request."""
        ...

    @property
    def user_id(self) -> int:
        """The authenticated user's id.

        Raises:
            RuntimeError: If the context has not been populated.
        """
        ...

    @property
    def role(self) -> user_enum.UserRole:
        """The authenticated user's role.

        Raises:
            RuntimeError: If the context has not been populated.
        """
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
