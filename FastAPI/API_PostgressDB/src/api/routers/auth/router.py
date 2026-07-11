from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["auth"])

from src.api.routers.auth import (  # noqa: E402
    login_route,  # noqa: F401
    refresh_token_route,  # noqa: F401
)
