from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, DatabaseException, NotFoundException
from app.db.models import Role


class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_roles(self):
        try:
            return self.db.query(Role).order_by(Role.name.asc()).all()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to load roles right now.") from exc

    def get_role_by_id(self, role_id: uuid.UUID):
        try:
            return self.db.query(Role).filter(Role.id == role_id).first()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to load the role right now.") from exc

    def get_role_by_name(self, name: str):
        try:
            return self.db.query(Role).filter(Role.name == name).first()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to load the role right now.") from exc

    def create_role(
        self,
        name: str,
        description: str | None = None,
        is_system_role: bool = False,
        is_active: bool = True,
    ):
        try:
            role = Role(
                name=name,
                description=description,
                is_system_role=is_system_role,
                is_active=is_active,
            )
            self.db.add(role)
            self.db.commit()
            self.db.refresh(role)
            return role
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException(
                message="A role with this name already exists.",
                code="role_already_exists",
            ) from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to create the role right now.") from exc

    def update_role(
        self,
        role_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        is_system_role: bool | None = None,
        is_active: bool | None = None,
    ):
        try:
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise NotFoundException(
                    message="Role not found.",
                    code="role_not_found",
                )

            if name is not None:
                role.name = name
            if description is not None:
                role.description = description
            if is_system_role is not None:
                role.is_system_role = is_system_role
            if is_active is not None:
                role.is_active = is_active

            self.db.commit()
            self.db.refresh(role)
            return role
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException(
                message="A role with this name already exists.",
                code="role_already_exists",
            ) from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to update the role right now.") from exc
