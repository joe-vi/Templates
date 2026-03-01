"""Abstract base class for structured application logging."""

from abc import ABC, abstractmethod


class CustomLoggerBase(ABC):
    """Abstract base class for structured application logging.

    Implement this interface with a provider-specific class (e.g. built-in
    logging, structlog, Datadog) and bind it in the DI container. Use cases
    depend only on this interface, so switching providers requires no changes
    outside the infrastructure layer.
    """

    @abstractmethod
    def info(self, message: str, **extra: object) -> None:
        """Log an informational message.

        Args:
            message: The log message.
            **extra: Additional key-value pairs to include in the log entry
                (e.g. user_id=123, request_id="abc").
        """

    @abstractmethod
    def warning(self, message: str, **extra: object) -> None:
        """Log a warning message.

        Args:
            message: The log message.
            **extra: Additional key-value pairs to include in the log entry.
        """

    @abstractmethod
    def error(
        self, message: str, exception: Exception | None = None, **extra: object
    ) -> None:
        """Log an error message.

        Args:
            message: The log message.
            exception: An optional exception whose traceback is included in
                the log entry.
            **extra: Additional key-value pairs to include in the log entry.
        """
