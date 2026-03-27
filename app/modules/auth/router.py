from fastapi import APIRouter, Depends, status

from app.modules.auth.dependencies import get_auth_service
from app.modules.auth.schema import LoginSchema, RegisterSchema
from app.modules.auth.service import AuthService

router = APIRouter()


@router.post("/login")
async def login(data: LoginSchema, auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.login(data.email, data.password)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: RegisterSchema, auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.register(data.username, data.email, data.password)
