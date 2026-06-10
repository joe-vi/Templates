"""bcrypt adapter implementing the password hasher port."""

from passlib.context import CryptContext


class BcryptPasswordHasher:
    """Password hasher backed by bcrypt (via passlib).

    To switch providers (e.g. argon2), implement the ``PasswordHasher`` port
    with a new adapter and update the dependency provider.
    """

    def __init__(self) -> None:
        self._context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, password: str) -> str:
        return self._context.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return self._context.verify(plain_password, hashed_password)
