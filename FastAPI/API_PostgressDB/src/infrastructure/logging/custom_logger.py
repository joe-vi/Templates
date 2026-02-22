import json
import logging
import uuid
from datetime import UTC, datetime

from injector import inject

from src.application.services.custom_logger_base import CustomLoggerBase
from src.application.services.user_context_base import UserContextBase
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

    The authenticated user_id is included in every log entry. Accessing the user_id
    before the user context is populated raises RuntimeError — use this logger only
    on routes protected by the JWT validation dependency.

    To switch providers (e.g. structlog, Datadog), create a new class that
    implements CustomLoggerBase and update the binding in container.py.
    """

    @inject
    def __init__(self, settings: Settings, user_context: UserContextBase) -> None:
        """Initialize the logger with a JSON stream handler and a unique request ID.

        A new UUID is generated on every instantiation. Because this class is
        request-scoped, each HTTP request gets its own UUID that is present on
        every log line emitted during that request.

        Args:
            settings: Application settings containing the log level configuration.
            user_context: Request-scoped context providing the authenticated user_id
                included in every log entry. Raises RuntimeError if the context has
                not been populated prior to logging.
        """
        self._logger = logging.getLogger("app")
        self._logger.setLevel(settings.log_level.upper())
        self._request_id = str(uuid.uuid4())
        self._user_context = user_context

        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(_JsonFormatter())
            self._logger.addHandler(handler)

    def _base_extra(self) -> dict[str, object]:
        fields: dict[str, object] = {"request_id": self._request_id}
        if self._user_context.is_populated:
            fields["user_id"] = self._user_context.user_id
        return fields

    def info(self, message: str, **extra: object) -> None:
        self._logger.info(message, extra={"extra": {**self._base_extra(), **extra}})

    def warning(self, message: str, **extra: object) -> None:
        self._logger.warning(message, extra={"extra": {**self._base_extra(), **extra}})

    def error(self, message: str, exception: Exception | None = None, **extra: object) -> None:
        self._logger.error(message, exc_info=exception, extra={"extra": {**self._base_extra(), **extra}})
