"""Unit tests for the request scope machinery (disposal, isolation)."""

import pytest
from injector import Binder, Injector, Module

from src.api.dependencies.request_scope import (
    _request_cache,
    async_request_scope,
    request,
    request_scope,
)


class _AsyncCloseOnly:
    """Resource exposing only an async close() — no aclose()."""

    def __init__(self) -> None:
        self.is_closed = False

    async def close(self) -> None:
        self.is_closed = True


class _AcloseResource:
    def __init__(self) -> None:
        self.is_aclosed = False
        self.is_closed = False

    async def aclose(self) -> None:
        self.is_aclosed = True

    def close(self) -> None:  # must NOT be preferred over aclose
        self.is_closed = True


class _SyncCloseResource:
    def __init__(self) -> None:
        self.is_closed = False

    def close(self) -> None:
        self.is_closed = True


class TestAsyncDisposal:
    async def test_async_close_without_aclose_is_awaited(self):
        """Regression: an async close() must be awaited, not leaked."""
        resource = _AsyncCloseOnly()
        async with async_request_scope():
            _request_cache.get()[_AsyncCloseOnly] = resource

        assert resource.is_closed is True

    async def test_aclose_is_preferred_over_close(self):
        resource = _AcloseResource()
        async with async_request_scope():
            _request_cache.get()[_AcloseResource] = resource

        assert resource.is_aclosed is True
        assert resource.is_closed is False

    async def test_sync_close_works_in_async_scope(self):
        resource = _SyncCloseResource()
        async with async_request_scope():
            _request_cache.get()[_SyncCloseResource] = resource

        assert resource.is_closed is True

    async def test_disposal_runs_in_reverse_creation_order(self):
        """Dependents are disposed before the dependencies they hold."""
        disposal_order: list[str] = []

        class First:
            def close(self) -> None:
                disposal_order.append("first")

        class Second:
            def close(self) -> None:
                disposal_order.append("second")

        async with async_request_scope():
            cache = _request_cache.get()
            cache[First] = First()
            cache[Second] = Second()

        assert disposal_order == ["second", "first"]

    async def test_failed_teardown_does_not_block_other_disposals(self):
        disposed: list[str] = []

        class Exploding:
            def close(self) -> None:
                raise RuntimeError("teardown boom")

        class WellBehaved:
            def close(self) -> None:
                disposed.append("ok")

        async with async_request_scope():
            cache = _request_cache.get()
            cache[WellBehaved] = WellBehaved()
            cache[Exploding] = Exploding()

        assert disposed == ["ok"]


class TestSyncDisposal:
    def test_sync_scope_disposes_sync_close(self):
        resource = _SyncCloseResource()
        with request_scope():
            _request_cache.get()[_SyncCloseResource] = resource

        assert resource.is_closed is True

    def test_sync_scope_does_not_call_async_close(self):
        """An async close() cannot be awaited from sync teardown; it must be
        skipped (with a warning) rather than left as a never-awaited
        coroutine."""
        resource = _AsyncCloseOnly()
        with request_scope():
            _request_cache.get()[_AsyncCloseOnly] = resource

        assert resource.is_closed is False


class _Counter:
    instances_created = 0

    def __init__(self) -> None:
        type(self).instances_created += 1


class _CounterModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(_Counter, scope=request)


class TestRequestScope:
    def test_one_instance_per_scope_and_fresh_between_scopes(self):
        _Counter.instances_created = 0
        injector = Injector([_CounterModule()])

        with request_scope():
            first = injector.get(_Counter)
            second = injector.get(_Counter)
        with request_scope():
            third = injector.get(_Counter)

        assert first is second
        assert third is not first
        assert _Counter.instances_created == 2

    def test_resolving_outside_scope_raises_helpful_error(self):
        injector = Injector([_CounterModule()])

        with pytest.raises(RuntimeError, match="outside a request scope"):
            injector.get(_Counter)
