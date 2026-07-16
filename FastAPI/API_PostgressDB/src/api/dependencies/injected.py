from typing import cast

from fastapi import Request, params


class Injected[T](params.Depends):
    """FastAPI dependency marker that resolves its interface from ``app.state.injector``."""

    def __init__(self, interface: type[T]) -> None:
        async def resolve_dependency(request: Request) -> T:
            return cast(T, request.app.state.injector.get(interface))

        super().__init__(dependency=resolve_dependency)
