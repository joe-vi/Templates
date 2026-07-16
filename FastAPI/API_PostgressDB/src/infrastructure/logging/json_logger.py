import json
import logging
from datetime import UTC, datetime

from injector import inject

from src.config.settings import Settings
from src.ports.logger import Logger
from src.ports.user_context import UserContext

_ALREADY_BOUND = "Logger.bind_request_id() was called more than once in the same request"
_UVICORN_LOGGERS = ("uvicorn", "uvicorn.error")


class _JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        extra: dict[str, object] = getattr(record, "extra", {})
        if extra:
            log_entry["extra"] = extra

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def configure_logging(settings: Settings) -> None:
    """Install the JSON handler on the root logger once at startup.

    Every logger in the process — application, uvicorn, third-party — propagates into the root
    handler, so the output stream carries a single machine-parseable format. Uvicorn's own access
    log is silenced in favour of the correlated line emitted by the ``access_log`` middleware.

    Args:
        settings: Application settings supplying the application log level.
    """
    _install_root_handler()
    _redirect_uvicorn_to_root()
    _silence_uvicorn_access_log()
    logging.getLogger().setLevel(logging.WARNING)
    logging.getLogger("app").setLevel(settings.log_level.upper())


def _install_root_handler() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    logging.getLogger().handlers = [handler]


def _redirect_uvicorn_to_root() -> None:
    for name in _UVICORN_LOGGERS:
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.propagate = True


def _silence_uvicorn_access_log() -> None:
    logging.getLogger("uvicorn.access").disabled = True


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
        user_id = self._user_context.user_id
        if user_id is not None:
            fields["user_id"] = user_id
        return fields

    def info(self, message: str, **extra: object) -> None:
        self._logger.info(message, extra={"extra": {**self._base_extra(), **extra}})

    def warning(self, message: str, **extra: object) -> None:
        self._logger.warning(message, extra={"extra": {**self._base_extra(), **extra}})

    def error(self, message: str, exception: Exception | None = None, **extra: object) -> None:
        self._logger.error(message, exc_info=exception, extra={"extra": {**self._base_extra(), **extra}})
