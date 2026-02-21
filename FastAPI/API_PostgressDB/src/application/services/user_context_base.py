from abc import ABC, abstractmethod

from src.domain.enums.user_enum import UserRole


class UserContextBase(ABC):
    """Request-scoped context holding the authenticated user's identity.

    Populated once per request by the JWT validation dependency after a valid
    Bearer token is verified. Any component — use case, service, or repository —
    can inject this interface to read the current user without threading raw
    token data through function signatures.

    Accessing any property before populate() is called raises RuntimeError.
    """

    @property
    @abstractmethod
    def user_id(self) -> int:
        """The unique identifier of the authenticated user."""

    @property
    @abstractmethod
    def username(self) -> str:
        """The username of the authenticated user."""

    @property
    @abstractmethod
    def role(self) -> UserRole:
        """The role of the authenticated user."""

    @abstractmethod
    def populate(self, user_id: int, username: str, role: UserRole) -> None:
        """Populate the context with decoded JWT claims.

        Called exactly once per request by the JWT validation dependency.

        Args:
            user_id: The authenticated user's unique identifier.
            username: The authenticated user's username.
            role: The authenticated user's role.
        """
