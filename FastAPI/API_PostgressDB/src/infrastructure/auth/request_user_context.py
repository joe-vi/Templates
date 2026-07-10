"""Request-scoped in-memory adapter for the user context port."""

from src.domain.enums import user_enum

_NOT_POPULATED = (
    "UserContext has not been populated — ensure the route is protected by "
    "the get_current_user guard"
)
_ALREADY_POPULATED = (
    "UserContext.populate() was called more than once in the same request"
)


class RequestUserContext:
    """Mutable request-scoped holder of the authenticated caller's identity.

    Bound at request scope, so every request starts with a fresh, empty
    instance and every component resolved in the same request shares it. The
    JWT guard calls populate() exactly once after validating the Bearer
    token; a second call raises RuntimeError to prevent accidental identity
    overwrites, and reading before populate() raises RuntimeError instead of
    returning missing or stale data.
    """

    def __init__(self) -> None:
        self._user_id: int | None = None
        self._role: user_enum.UserRole | None = None

    @property
    def is_populated(self) -> bool:
        return self._user_id is not None

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
        if self._user_id is not None:
            raise RuntimeError(_ALREADY_POPULATED)
        self._user_id = user_id
        self._role = role
