import json
import logging
from datetime import UTC, datetime

from injector import inject

from src.application.services.logger import Logger
from src.application.services.user_context import UserContext
from src.config.settings import Settings

_ALREADY_BOUND = "Logger.bind_request_id() was called more than once in the same request"


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


def configure_logging(settings: Settings) -> None:
    """Configure the process-wide ``app`` logger once at startup.

    Args:
        settings: Application settings supplying the log level.
    """
    logger = logging.getLogger("app")
    logger.setLevel(settings.log_level.upper())
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)


class JsonLogger(Logger):
    """``Logger`` adapter emitting structured JSON via the stdlib logging module."""

    @inject
    def __init__(self, user_context: UserContext) -> None:
        self._logger = logging.getLogger("app")
        self._user_context = user_context
        self._request_id: str | None = None

    def bind_request_id(self, request_id: str) -> None:
        if self._request_id is not None:
            raise RuntimeError(_ALREADY_BOUND)
        self._request_id = request_id

    def _base_extra(self) -> dict[str, object]:
        fields: dict[str, object] = {}
        if self._request_id is not None:
            fields["request_id"] = self._request_id
        if self._user_context.is_populated:
            fields["user_id"] = self._user_context.user_id
        return fields

    def info(self, message: str, **extra: object) -> None:
        self._logger.info(message, extra={"extra": {**self._base_extra(), **extra}})

    def warning(self, message: str, **extra: object) -> None:
        self._logger.warning(message, extra={"extra": {**self._base_extra(), **extra}})

    def error(self, message: str, exception: Exception | None = None, **extra: object) -> None:
        self._logger.error(message, exc_info=exception, extra={"extra": {**self._base_extra(), **extra}})
