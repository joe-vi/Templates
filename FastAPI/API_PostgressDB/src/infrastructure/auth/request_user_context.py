from src.domain.enums import user_enum
from src.ports.user_context import UserContext

_ALREADY_POPULATED = "UserContext.populate() was called more than once in the same request"


class RequestUserContext(UserContext):
    """``UserContext`` adapter: a mutable request-scoped identity holder."""

    def __init__(self) -> None:
        self._user_id: int | None = None
        self._role: user_enum.UserRole | None = None

    @property
    def user_id(self) -> int | None:
        return self._user_id

    @property
    def role(self) -> user_enum.UserRole | None:
        return self._role

    def populate(self, user_id: int, role: user_enum.UserRole) -> None:
        if self._user_id is not None:
            raise RuntimeError(_ALREADY_POPULATED)
        self._user_id = user_id
        self._role = role
