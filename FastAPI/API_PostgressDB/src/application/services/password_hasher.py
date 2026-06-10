"""Password hashing port (structural interface)."""

from typing import Protocol


class PasswordHasher(Protocol):
    """Port for password hashing.

    Implement with a provider-specific adapter (e.g. bcrypt, argon2) and wire
    it in the dependency providers. Use cases depend only on this protocol, so
    switching providers requires no changes outside the infrastructure layer.
    """

    def hash(self, password: str) -> str:
        """Hash a plain-text password.

        Args:
            password: The plain-text password to hash.

        Returns:
            The hashed password string.
        """
        ...

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain-text password against a hashed password.

        Args:
            plain_password: The plain-text password to verify.
            hashed_password: The hashed password to compare against.

        Returns:
            True if the password matches, False otherwise.
        """
        ...
