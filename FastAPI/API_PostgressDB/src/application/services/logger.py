from typing import Protocol


class Logger(Protocol):
    """Port for structured application logging.

    Implemented by a mechanism-qualified adapter (e.g. stdlib logging,
    structlog, Datadog) that subclasses this protocol and inherits these
    docstrings. Adapters are expected to attach per-request correlation
    (request id, authenticated user id) to every entry.
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

    def error(self, message: str, exception: Exception | None = None, **extra: object) -> None:
        """Log an error message.

        Args:
            message: The log message.
            exception: An optional exception whose traceback is included.
            **extra: Additional key-value pairs to include in the log entry.
        """
        ...
