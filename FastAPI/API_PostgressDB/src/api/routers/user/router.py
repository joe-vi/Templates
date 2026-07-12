from fastapi import APIRouter, Depends

from src.api.dependencies.jwt_dependency import get_current_user
from src.api.routers.user import create_user_route, delete_user_route, get_all_users_route, get_user_route, update_user_role_route

router = APIRouter(prefix="/api/v1", tags=["users"], dependencies=[Depends(get_current_user)])
router.include_router(create_user_route.router, prefix="/users")
router.include_router(get_user_route.router, prefix="/users")
router.include_router(get_all_users_route.router, prefix="/users")
router.include_router(update_user_role_route.router, prefix="/users")
router.include_router(delete_user_route.router, prefix="/users")
