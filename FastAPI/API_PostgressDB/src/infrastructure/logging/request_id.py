from dataclasses import dataclass


@dataclass(frozen=True)
class RequestId:
    """Correlation id bound to one request; provided per request and injected into the logger."""

    value: str
