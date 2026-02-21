from passlib.context import CryptContext

from src.application.services.password_hasher_base import PasswordHasherBase


class PasswordHasher(PasswordHasherBase):
    """bcrypt password hasher using passlib.

    To switch providers (e.g. argon2), create a new class that implements
    PasswordHasherBase and update the binding in container.py.
    """

    def __init__(self) -> None:
        self._context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, password: str) -> str:
        return self._context.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return self._context.verify(plain_password, hashed_password)
