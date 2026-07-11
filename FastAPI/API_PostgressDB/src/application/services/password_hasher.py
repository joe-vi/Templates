from typing import Protocol


class PasswordHasher(Protocol):
    """Port for password hashing.

    Implemented by a mechanism-qualified adapter (e.g. bcrypt, argon2) that
    subclasses this protocol and inherits these docstrings — document the
    contract here only. Use cases depend on this port, so switching providers
    requires no change outside the infrastructure layer.
    """

    def hash(self, password: str) -> str:
        """Hash a plain-text password.

        Args:
            password: The plain-text password to hash.

        Returns:
            The hashed password string, safe to store.
        """
        ...

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain-text password against a stored hash.

        Args:
            plain_password: The plain-text password to verify.
            hashed_password: The stored hash to compare against.

        Returns:
            True if the password matches, False otherwise.
        """
        ...
