import json
import logging
import uuid
from datetime import UTC, datetime

from injector import inject

from src.application.services.custom_logger_base import CustomLoggerBase
from src.config.settings import Settings


class _JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        extra: dict[str, object] = getattr(record, "extra", {})
        if extra:
            log_entry["extra"] = extra

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class CustomLogger(CustomLoggerBase):
    """Structured JSON logger using Python's built-in logging module.

    Request-scoped: a new instance is created per HTTP request, each with a unique
    request_id UUID that is automatically included in every log entry, making it
    easy to trace all logs belonging to a single request.

    To switch providers (e.g. structlog, Datadog), create a new class that
    implements CustomLoggerBase and update the binding in container.py.
    """

    @inject
    def __init__(self, settings: Settings) -> None:
        """Initialize the logger with a JSON stream handler and a unique request ID.

        A new UUID is generated on every instantiation. Because this class is
        request-scoped, each HTTP request gets its own UUID that is present on
        every log line emitted during that request.

        Args:
            settings: Application settings containing the log level configuration.
        """
        self._logger = logging.getLogger("app")
        self._logger.setLevel(settings.log_level.upper())
        self._request_id = str(uuid.uuid4())

        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(_JsonFormatter())
            self._logger.addHandler(handler)

    def info(self, message: str, **extra: object) -> None:
        self._logger.info(message, extra={"extra": {"request_id": self._request_id, **extra}})

    def warning(self, message: str, **extra: object) -> None:
        self._logger.warning(message, extra={"extra": {"request_id": self._request_id, **extra}})

    def error(self, message: str, exception: Exception | None = None, **extra: object) -> None:
        self._logger.error(message, exc_info=exception, extra={"extra": {"request_id": self._request_id, **extra}})
