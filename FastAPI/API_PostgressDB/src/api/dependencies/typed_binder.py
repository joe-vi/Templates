"""Statically-typed facade over the injector Binder.

Passing an implementation that does not satisfy its port is a type-checker
error at the call site (dev time and CI). There is no runtime conformance
check, and no graph-completeness check: a missing binding surfaces as a
runtime error on first resolution.
"""

from __future__ import annotations

from typing import Any


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
