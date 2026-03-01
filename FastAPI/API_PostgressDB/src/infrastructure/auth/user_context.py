"""Request-scoped implementation of the user context."""

from src.application.services import user_context_base
from src.domain.enums import user_enum

_NOT_POPULATED = (
    "UserContext has not been populated"
    " — ensure the route is protected by get_current_user"
)
_ALREADY_POPULATED = (
    "UserContext.populate() was called more than once in the same request"
)


class UserContext(user_context_base.UserContextBase):
    """Mutable request-scoped implementation of UserContextBase.

    Starts empty on every request. The JWT validation dependency
    (get_current_user) calls populate() exactly once after decoding the Bearer
    token, making the authenticated user's identity available to any injected
    component for the lifetime of that request.

    Calling populate() a second time within the same request raises
    RuntimeError to prevent accidental overwrites of the authenticated identity.

    To switch the backing store (e.g. read from a header directly, cache in
    Redis), create a new class that implements UserContextBase and update the
    binding in container.py.
    """

    def __init__(self) -> None:
        self._user_id: int | None = None
        self._role: user_enum.UserRole | None = None
        self._is_populated: bool = False

    @property
    def is_populated(self) -> bool:
        return self._is_populated

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise RuntimeError(_NOT_POPULATED)
        return self._user_id

    @property
    def role(self) -> user_enum.UserRole:
        if self._role is None:
            raise RuntimeError(_NOT_POPULATED)
        return self._role

    def populate(self, user_id: int, role: user_enum.UserRole) -> None:
        if self._is_populated:
            raise RuntimeError(_ALREADY_POPULATED)
        self._user_id = user_id
        self._role = role
        self._is_populated = True
