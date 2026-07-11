from fastapi import APIRouter, Depends

from src.api.dependencies.jwt_dependency import get_current_user

router = APIRouter(prefix="/api/v1", tags=["users"], dependencies=[Depends(get_current_user)])

from src.api.routers.user import (  # noqa: E402
    create_user_route,  # noqa: F401
    delete_user_route,  # noqa: F401
    get_all_users_route,  # noqa: F401
    get_user_route,  # noqa: F401
    update_user_role_route,  # noqa: F401
)
