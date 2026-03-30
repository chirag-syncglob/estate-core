from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundException
from app.modules.roles.constants import DEFAULT_SYSTEM_ROLES
from app.modules.roles.repository import RoleRepository


class RoleService:
    def __init__(self, role_repository: RoleRepository):
        self.role_repository = role_repository

    @staticmethod
    def _normalize_name(name: str) -> str:
        return name.strip().upper()

    @staticmethod
    def _build_role_response(role):
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_system_role": role.is_system_role,
            "is_active": role.is_active,
        }

    def list_roles(self):
        roles = self.role_repository.list_roles()
        return [self._build_role_response(role) for role in roles]

    def get_role(self, role_id: uuid.UUID):
        role = self.role_repository.get_role_by_id(role_id)
        if not role:
            raise NotFoundException(
                message="Role not found.",
                code="role_not_found",
            )

        return self._build_role_response(role)

    def create_role(
        self,
        name: str,
        description: str | None = None,
        is_system_role: bool = False,
        is_active: bool = True,
    ):
        role = self.role_repository.create_role(
            name=self._normalize_name(name),
            description=description,
            is_system_role=is_system_role,
            is_active=is_active,
        )
        return self._build_role_response(role)

    def update_role(
        self,
        role_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        is_system_role: bool | None = None,
        is_active: bool | None = None,
    ):
        normalized_name = self._normalize_name(name) if name is not None else None
        role = self.role_repository.update_role(
            role_id=role_id,
            name=normalized_name,
            description=description,
            is_system_role=is_system_role,
            is_active=is_active,
        )
        return self._build_role_response(role)

    def seed_default_roles(self):
        created = 0
        updated = 0
        seeded_roles = []

        for role_data in DEFAULT_SYSTEM_ROLES:
            normalized_name = self._normalize_name(role_data["name"])
            existing_role = self.role_repository.get_role_by_name(normalized_name)

            if existing_role:
                needs_update = any(
                    [
                        existing_role.description != role_data["description"],
                        existing_role.is_system_role is not True,
                        existing_role.is_active is not True,
                    ]
                )

                if needs_update:
                    existing_role = self.role_repository.update_role(
                        role_id=existing_role.id,
                        description=role_data["description"],
                        is_system_role=True,
                        is_active=True,
                    )
                    updated += 1

                seeded_roles.append(self._build_role_response(existing_role))
                continue

            created_role = self.role_repository.create_role(
                name=normalized_name,
                description=role_data["description"],
                is_system_role=True,
                is_active=True,
            )
            created += 1
            seeded_roles.append(self._build_role_response(created_role))

        return {
            "message": "Roles seeded successfully.",
            "created": created,
            "updated": updated,
            "roles": seeded_roles,
        }
