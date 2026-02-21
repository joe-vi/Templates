from abc import ABC, abstractmethod


class PasswordHasherBase(ABC):
    """Abstract base class for password hashing operations.

    Implement this interface with a provider-specific class (e.g. bcrypt, argon2) and
    bind it in the DI container. Use cases depend only on this interface, so switching
    providers requires no changes outside the infrastructure layer.
    """

    @abstractmethod
    def hash(self, password: str) -> str:
        """Hash a plain-text password.

        Args:
            password: The plain-text password to hash.

        Returns:
            The hashed password string.
        """

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain-text password against a hashed password.

        Args:
            plain_password: The plain-text password to verify.
            hashed_password: The hashed password to compare against.

        Returns:
            True if the password matches, False otherwise.
        """
