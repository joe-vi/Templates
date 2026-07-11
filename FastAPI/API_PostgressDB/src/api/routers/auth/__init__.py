from fastapi import APIRouter

from src.api.routers.auth import login_route, refresh_token_route

# One route module per operation; the prefix and tag are declared once here.
# No JWT guard: these endpoints are how callers obtain tokens.
router = APIRouter(prefix="/api/v1", tags=["auth"])
router.include_router(login_route.router)
router.include_router(refresh_token_route.router)
