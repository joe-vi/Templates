from fastapi import APIRouter

from src.api.routers.auth import login_route, refresh_token_route

router = APIRouter(prefix="/api/v1", tags=["auth"])
router.include_router(login_route.router)
router.include_router(refresh_token_route.router)
