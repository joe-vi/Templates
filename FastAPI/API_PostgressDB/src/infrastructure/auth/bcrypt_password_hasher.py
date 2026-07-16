from passlib.context import CryptContext

from src.ports.password_hasher import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    """``PasswordHasher`` adapter backed by bcrypt (via passlib)."""

    def __init__(self) -> None:
        self._context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, password: str) -> str:
        return self._context.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return self._context.verify(plain_password, hashed_password)
