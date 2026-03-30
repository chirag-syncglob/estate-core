from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.roles.repository import RoleRepository
from app.modules.roles.service import RoleService


def get_role_repository(db: Session = Depends(get_db)) -> RoleRepository:
    return RoleRepository(db)


def get_role_service(
    role_repository: RoleRepository = Depends(get_role_repository),
) -> RoleService:
    return RoleService(role_repository)
