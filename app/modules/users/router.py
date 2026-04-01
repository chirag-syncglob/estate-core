from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.modules.auth.dependencies import require_roles
from app.modules.users.dependencies import get_user_service
from app.modules.users.schema import CreateUserSchema, UpdateUserSchema
from app.modules.users.service import UserService


router = APIRouter(dependencies=[Depends(require_roles("COMPANY_ADMIN"))])

@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_user(
    data: CreateUserSchema,
    user_service: UserService = Depends(get_user_service),
):
    user = user_service.create_user(
        name=data.name,
        email=data.email,
        role_id=data.role_id,
    )
    return {
        "message": "User created successfully. An account setup OTP has been sent to the user email.",
        "user_id": str(user.id),
    }

@router.get("/all")
def get_all_users(
    user_service: UserService = Depends(get_user_service),
):
    users = user_service.get_all_users()
    return {"users": users}

@router.put("/update/{user_id}")
def update_user(
    user_id: UUID,
    data: UpdateUserSchema,
    user_service: UserService = Depends(get_user_service),
):
    user = user_service.update_user(
        user_id=user_id,
        name=data.name,
        email=data.email,
        role_id=data.role_id,
        is_active=data.is_active,
    )
    return {"message": "User updated successfully", "user_id": str(user.id)}
    
@router.get("/{user_id}")
def get_user_by_id(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
):
    return {"user": user_service.get_user_by_id(user_id)}
