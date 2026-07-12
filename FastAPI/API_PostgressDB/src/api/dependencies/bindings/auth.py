from src.application.use_cases.auth.login_use_case import LoginUseCase
from src.application.use_cases.auth.refresh_token_use_case import RefreshTokenUseCase
from src.infrastructure.di.typed_binder import TypedBinder


def register(typed_binder: TypedBinder) -> None:
    """Bind the auth domain's use cases (all transient)."""
    typed_binder.bind_self_typed(LoginUseCase)
    typed_binder.bind_self_typed(RefreshTokenUseCase)
