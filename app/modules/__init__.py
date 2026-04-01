from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.roles.router import router as roles_router
from app.modules.users.router import router as users_router

api_router = APIRouter()

api_router.include_router(
    prefix="/auth",
    tags=["auth"],
    router=auth_router
)

api_router.include_router(
    prefix="/roles",
    tags=["roles"],
    router=roles_router,
)

api_router.include_router(
    prefix="/users",
    tags=["users"],
    router=users_router,
)
