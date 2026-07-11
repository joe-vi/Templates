from injector import Binder, Injector, Module, singleton

from src.infrastructure.di.typed_binder import TypedBinder


class _Port:
    """Stand-in port for TypedBinder wiring tests."""

    def greet(self) -> str:  # pragma: no cover - interface only
        raise NotImplementedError


class _Adapter(_Port):
    def greet(self) -> str:
        return "hello"


class TestTypedBinder:
    def test_bound_port_resolves_to_implementation(self):
        class WiringModule(Module):
            def configure(self, binder: Binder) -> None:
                typed_binder = TypedBinder(binder)
                typed_binder.bind_typed(_Port).to(_Adapter, scope=singleton)

        injector = Injector([WiringModule()])

        resolved = injector.get(_Port)

        assert isinstance(resolved, _Adapter)
        assert resolved.greet() == "hello"

    def test_bind_self_typed_resolves_concrete_class(self):
        class WiringModule(Module):
            def configure(self, binder: Binder) -> None:
                TypedBinder(binder).bind_self_typed(_Adapter, scope=singleton)

        injector = Injector([WiringModule()])

        assert isinstance(injector.get(_Adapter), _Adapter)
