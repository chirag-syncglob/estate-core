import uuid

from fastapi import APIRouter, Depends, status

from app.modules.auth.dependencies import get_current_user_id
from app.modules.roles.dependencies import get_role_service
from app.modules.roles.schema import RoleCreateSchema, RoleUpdateSchema
from app.modules.roles.service import RoleService

router = APIRouter(dependencies=[Depends(get_current_user_id)])


@router.get("")
async def list_roles(role_service: RoleService = Depends(get_role_service)):
    return role_service.list_roles()


@router.get("/{role_id}")
async def get_role(role_id: uuid.UUID, role_service: RoleService = Depends(get_role_service)):
    return role_service.get_role(role_id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_role(
    data: RoleCreateSchema,
    role_service: RoleService = Depends(get_role_service),
):
    return role_service.create_role(
        name=data.name,
        description=data.description,
        is_system_role=data.is_system_role,
        is_active=data.is_active,
    )


@router.patch("/{role_id}")
async def update_role(
    role_id: uuid.UUID,
    data: RoleUpdateSchema,
    role_service: RoleService = Depends(get_role_service),
):
    return role_service.update_role(
        role_id=role_id,
        name=data.name,
        description=data.description,
        is_system_role=data.is_system_role,
        is_active=data.is_active,
    )
