from typing import Protocol


class Logger(Protocol):
    """Port for structured application logging."""

    def bind_request_id(self, request_id: str) -> None:
        """Bind the correlation id for the current request.

        Args:
            request_id: The correlation id to attach to every log entry.

        Raises:
            RuntimeError: If a request id was already bound.
        """
        ...

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

    def error(self, message: str, exception: Exception | None = None, **extra: object) -> None:
        """Log an error message.

        Args:
            message: The log message.
            exception: An optional exception whose traceback is included.
            **extra: Additional key-value pairs to include in the log entry.
        """
        ...
