from typing import Any, cast

from fastapi import Depends, Request


def Injected[T](interface: type[T]) -> Any:  # noqa: N802 - mirrors Depends()
    """Resolve ``interface`` from the app's injector, per request.

    Args:
        interface: The type to resolve from the injector.

    Returns:
        A FastAPI ``Depends`` that resolves ``interface`` for each request.
    """

    async def resolve_dependency(request: Request) -> T:
        return cast(T, request.app.state.injector.get(interface))

    return Depends(resolve_dependency)
