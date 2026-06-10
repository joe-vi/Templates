"""Structured logging port (structural interface)."""

from typing import Protocol


class Logger(Protocol):
    """Port for structured application logging.

    Implement with a provider-specific adapter (e.g. built-in logging,
    structlog, Datadog) and wire it in the dependency providers. Use cases
    depend only on this protocol, so switching providers requires no changes
    outside the infrastructure layer.
    """

    def info(self, message: str, **extra: object) -> None:
        """Log an informational message.

        Args:
            message: The log message.
            **extra: Additional key-value pairs to include in the log entry.
        """
        ...

    def warning(self, message: str, **extra: object) -> None:
        """Log a warning message.

        Args:
            message: The log message.
            **extra: Additional key-value pairs to include in the log entry.
        """
        ...

    def error(
        self, message: str, exception: Exception | None = None, **extra: object
    ) -> None:
        """Log an error message.

        Args:
            message: The log message.
            exception: An optional exception whose traceback is included.
            **extra: Additional key-value pairs to include in the log entry.
        """
        ...
