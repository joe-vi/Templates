"""bcrypt implementation of the password hasher."""

from injector import inject
from passlib.context import CryptContext

from src.application.services import password_hasher_base


class PasswordHasher(password_hasher_base.PasswordHasherBase):
    """bcrypt password hasher using passlib.

    To switch providers (e.g. argon2), create a new class that implements
    PasswordHasherBase and update the binding in container.py.
    """

    @inject
    def __init__(self) -> None:
        self._context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, password: str) -> str:
        return self._context.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return self._context.verify(plain_password, hashed_password)
