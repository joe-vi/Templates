import json
import logging
from datetime import UTC, datetime

from injector import inject

from src.application.services.logger import Logger
from src.config.settings import Settings
from src.infrastructure.logging import log_context


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


class JsonLogger(Logger):
    """``Logger`` adapter emitting structured JSON via the stdlib logging module."""

    @inject
    def __init__(self, settings: Settings) -> None:
        self._logger = logging.getLogger("app")
        self._logger.setLevel(settings.log_level.upper())

        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(_JsonFormatter())
            self._logger.addHandler(handler)

    def _base_extra(self) -> dict[str, object]:
        fields: dict[str, object] = {}
        request_id = log_context.request_id_var.get()
        if request_id is not None:
            fields["request_id"] = request_id
        user_id = log_context.user_id_var.get()
        if user_id is not None:
            fields["user_id"] = user_id
        return fields

    def info(self, message: str, **extra: object) -> None:
        self._logger.info(message, extra={"extra": {**self._base_extra(), **extra}})

    def warning(self, message: str, **extra: object) -> None:
        self._logger.warning(message, extra={"extra": {**self._base_extra(), **extra}})

    def error(self, message: str, exception: Exception | None = None, **extra: object) -> None:
        self._logger.error(message, exc_info=exception, extra={"extra": {**self._base_extra(), **extra}})
