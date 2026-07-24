from typing import TYPE_CHECKING, Annotated, cast

from fastapi import Request, params

if TYPE_CHECKING:
    type Injected[T] = T
    """Marks a route parameter for resolution from ``app.state.injector``; the parameter's type is ``T`` itself."""
else:

    class Injected:
        """Statically the identity alias above; at runtime subscripting builds the ``Annotated`` form FastAPI resolves."""

        def __class_getitem__(cls, interface):
            return Annotated[interface, _InjectedDependency(interface)]


class _InjectedDependency[T](params.Depends):
    """FastAPI dependency marker that resolves its interface from ``app.state.injector``."""

    def __init__(self, interface: type[T]) -> None:
        async def resolve_dependency(request: Request) -> T:
            return cast(T, request.app.state.injector.get(interface))

        super().__init__(dependency=resolve_dependency)
