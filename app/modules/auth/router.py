import uuid

from fastapi import APIRouter, Depends, status

from app.modules.auth.dependencies import get_auth_service, get_current_user_id
from app.modules.auth.schema import (
    ChangePasswordSchema,
    ForgotPasswordSchema,
    LoginSchema,
    RefreshTokenSchema,
    RegisterSchema,
    ResetPasswordSchema,
)
from app.modules.auth.service import AuthService

router = APIRouter()


@router.post("/login")
async def login(data: LoginSchema, auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.login(data.email, data.password)


@router.post("/refresh")
async def refresh_tokens(
    data: RefreshTokenSchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.refresh_tokens(data.refresh_token)


@router.get("/me")
async def get_current_user(
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.get_current_user(current_user_id)


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordSchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.forgot_password(data.email)


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordSchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.reset_password(
        email=data.email,
        otp=data.otp,
        new_password=data.new_password,
    )


@router.post("/change-password")
async def change_password(
    data: ChangePasswordSchema,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.change_password(
        user_id=current_user_id,
        old_password=data.old_password,
        new_password=data.new_password,
    )
