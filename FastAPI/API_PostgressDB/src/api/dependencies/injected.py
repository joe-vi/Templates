from typing import Any, cast

from fastapi import Depends, Request


def Injected[T](interface: type[T]) -> Any:  # noqa: N802 - mirrors Depends()
    """Resolve ``interface`` from the app's injector, per request.

    Usage in a route or FastAPI dependency signature::

        use_case: Annotated[CreateUserUseCase, Injected(CreateUserUseCase)]
    """

    async def resolve_dependency(request: Request) -> T:
        return cast(T, request.app.state.injector.get(interface))

    return Depends(resolve_dependency)
