from __future__ import annotations

import contextvars
import inspect
import logging
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from typing import Any

from injector import InstanceProvider, Provider, Scope, ScopeDecorator

logger = logging.getLogger(__name__)


_request_cache: contextvars.ContextVar[dict[type, Any]] = contextvars.ContextVar("injector_request_cache")


class RequestScope(Scope):
    """One instance per key per active request context."""

    def get[T](self, key: type[T], provider: Provider[T]) -> Provider[T]:
        try:
            cache = _request_cache.get()
        except LookupError as exc:
            raise RuntimeError(
                f"{key!r} is request-scoped but was resolved outside a request scope. "
                "Enter one with `with request_scope():` (sync) or `async with async_request_scope():` (async) first."
            ) from exc
        if key not in cache:
            cache[key] = provider.get(self.injector)
        return InstanceProvider(cache[key])


request = ScopeDecorator(RequestScope)


def _dispose_sync(instance: Any) -> None:
    close = getattr(instance, "close", None)
    if not callable(close):
        return
    if inspect.iscoroutinefunction(close):
        # A coroutine cannot be awaited from sync teardown; calling it would
        # silently create a never-awaited coroutine and leak the resource.
        logger.warning("cannot dispose %r in a sync request scope: close() is async", instance)
        return
    close()


async def _dispose_async(instance: Any) -> None:
    aclose = getattr(instance, "aclose", None)
    if callable(aclose):
        aclose_result = aclose()
        if inspect.isawaitable(aclose_result):
            await aclose_result
        return
    close = getattr(instance, "close", None)
    if not callable(close):
        return
    # close() may be sync or async (awaitable result); support both so an
    # async close without aclose() is not silently left un-awaited.
    close_result = close()
    if inspect.isawaitable(close_result):
        await close_result


@contextmanager
def request_scope() -> Generator[None]:
    """Enter a per-request scope for synchronous (WSGI) code.

    Disposes every request-scoped object on exit, in reverse creation order.
    """
    cache: dict[type, Any] = {}
    token = _request_cache.set(cache)
    try:
        yield
    finally:
        try:
            for instance in reversed(list(cache.values())):
                try:
                    _dispose_sync(instance)
                except Exception:
                    logger.exception("request-scoped teardown failed for %r", instance)
        finally:
            _request_cache.reset(token)


@asynccontextmanager
async def async_request_scope() -> AsyncGenerator[None]:
    """Enter a per-request scope for asynchronous (ASGI) code.

    Disposes every request-scoped object on exit, in reverse creation order.
    """
    cache: dict[type, Any] = {}
    token = _request_cache.set(cache)
    try:
        yield
    finally:
        try:
            for instance in reversed(list(cache.values())):
                try:
                    await _dispose_async(instance)
                except Exception:
                    logger.exception("request-scoped teardown failed for %r", instance)
        finally:
            _request_cache.reset(token)
