"""Request-scoped dependency injection built on the injector library.

Provides three pieces:

- ``RequestScope`` / ``request``: one instance per key per active request,
  with state held in a ``ContextVar`` for correct isolation under asyncio.
- ``request_scope()`` / ``async_request_scope()``: context managers that open
  a per-request cache and dispose every request-scoped object on exit.
- ``TypedBinder``: a statically-typed facade over the injector ``Binder`` so
  a binding whose implementation does not satisfy its port is a type-checker
  error at the call site.

``Injected(Interface)`` is the route-side accessor: a thin ``Depends`` that
resolves the interface from ``request.app.state.injector``.
"""

from __future__ import annotations

import contextvars
import inspect
import logging
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from typing import Any, cast

from fastapi import Depends, Request
from injector import InstanceProvider, Provider, Scope, ScopeDecorator

logger = logging.getLogger(__name__)


_request_cache: contextvars.ContextVar[dict[type, Any]] = (
    contextvars.ContextVar("injector_request_cache")
)


class RequestScope(Scope):
    """One instance per key per active request context.

    The per-request cache is not stored on this object. injector keeps a
    single Scope instance for the injector's whole life, so storing state
    here would make it behave like a singleton shared by every request.
    State lives in a ContextVar instead, giving correct per-request isolation
    under both threads and asyncio tasks.
    """

    def get[T](self, key: type[T], provider: Provider[T]) -> Provider[T]:
        try:
            cache = _request_cache.get()
        except LookupError as exc:
            raise RuntimeError(
                f"{key!r} is request-scoped but was resolved outside a "
                "request scope. Enter one with `with request_scope():` "
                "(sync) or `async with async_request_scope():` (async) "
                "first."
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
        logger.warning(
            "cannot dispose %r in a sync request scope: close() is async",
            instance,
        )
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
def request_scope() -> Iterator[None]:
    """Enter a per-request scope for synchronous (WSGI) code.

    On exit, every request-scoped object is disposed independently, in
    reverse creation order (dependents before their dependencies): a failure
    in one object's ``close()`` is logged and does not prevent the others
    from being disposed, and the scope is always reset.
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
                    logger.exception(
                        "request-scoped teardown failed for %r", instance
                    )
        finally:
            _request_cache.reset(token)


@asynccontextmanager
async def async_request_scope() -> AsyncIterator[None]:
    """Enter a per-request scope for asynchronous (ASGI) code.

    Disposes request-scoped objects on exit, preferring an async ``aclose()``
    and falling back to ``close()`` (awaited when it returns an awaitable).
    Objects are disposed independently, in reverse creation order: a failure
    in one is logged and does not prevent the others from being disposed,
    and the scope is always reset.
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
                    logger.exception(
                        "request-scoped teardown failed for %r", instance
                    )
        finally:
            _request_cache.reset(token)


class _Binding[P]:
    """Returned by ``TypedBinder.bind_typed``; records the binding when
    ``to`` (a single implementation) or ``to_many`` (a collection) is called.

    The type variable P is fixed by the interface passed to ``bind_typed``,
    so both methods require implementations of type[P] and a mismatch is a
    type-checker error.
    """

    def __init__(self, binder: Any, interface: type[P]) -> None:
        self._binder = binder
        self._interface = interface

    def to(self, impl: type[P], scope: Any = None) -> None:
        self._binder.bind(self._interface, to=impl, scope=scope)

    def to_many(self, impls: list[type[P]], scope: Any = None) -> None:
        self._binder.multibind(
            list[self._interface],  # type: ignore[name-defined]
            to=list(impls),
            scope=scope,
        )


class TypedBinder:
    """Statically-typed facade over an injector Binder.

    Passing a class that does not satisfy the port is a type-checker error at
    the call site (dev time and CI). There is no runtime conformance check,
    and no graph-completeness check: a missing binding surfaces as a runtime
    error on first resolution.

        typed_binder = TypedBinder(binder)
        typed_binder.bind_typed(UserRepository).to(
            SqlAlchemyUserRepository, scope=request
        )
        typed_binder.bind_self_typed(UserUseCase, scope=request)

    ``bind_typed`` returns a small builder whose ``to``/``to_many`` methods
    record the binding. The type variable P is solved solely from the
    interface passed to ``bind_typed``, so ``to``/``to_many`` require an
    implementation of type[P]. A single flat method bind_typed(interface,
    impl) would not work: the checker would infer P as a common supertype of
    both arguments and report no error.

    Any other Binder method (bind_scope, install, and so on) passes straight
    through.
    """

    def __init__(self, binder: Any) -> None:
        self._binder = binder

    def bind_typed[P](self, interface: type[P]) -> _Binding[P]:
        return _Binding(self._binder, interface)

    def bind_self_typed[P](self, cls: type[P], scope: Any = None) -> None:
        """Bind a concrete class to itself (no separate port)."""
        self._binder.bind(cls, to=cls, scope=scope)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._binder, name)


def Injected[T](interface: type[T]) -> Any:  # noqa: N802 - mirrors Depends()
    """Route-side accessor: resolve ``interface`` from the app's injector.

    Usage in a route or FastAPI dependency signature::

        use_case: UserUseCase = Injected(UserUseCase)

    Resolution happens per request, inside the request scope entered by the
    middleware in ``main.py``, so request-scoped bindings work as expected.
    """

    async def resolve_dependency(request: Request) -> T:
        return cast(T, request.app.state.injector.get(interface))

    return Depends(resolve_dependency)
