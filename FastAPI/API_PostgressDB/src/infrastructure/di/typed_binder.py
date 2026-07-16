from __future__ import annotations

from typing import Any


class _Binding[P]:
    """Records a binding: ``to`` for one implementation, ``to_many`` for a collection."""

    def __init__(self, binder: Any, interface: type[P]) -> None:
        self._binder = binder
        self._interface = interface

    def to(self, impl: type[P], scope: Any = None) -> None:
        self._binder.bind(self._interface, to=impl, scope=scope)

    def to_many(self, impls: list[type[P]], scope: Any = None) -> None:
        self._binder.multibind(list[self._interface], to=list(impls), scope=scope)


class TypedBinder:
    """Statically-typed facade over an injector Binder."""

    def __init__(self, binder: Any) -> None:
        self._binder = binder

    def bind_typed[P](self, interface: type[P]) -> _Binding[P]:
        return _Binding(self._binder, interface)

    def bind_self_typed[P](self, cls: type[P], scope: Any = None) -> None:
        """Bind a concrete class to itself (no separate port)."""
        self._binder.bind(cls, to=cls, scope=scope)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._binder, name)
