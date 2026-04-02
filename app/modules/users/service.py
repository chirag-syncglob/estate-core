from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from app.core.exceptions import (
    AppException,
    AuthorizationException,
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.modules.auth.dependencies import AuthContext
from app.modules.auth.repository import AuthRepository
from app.modules.roles.repository import RoleRepository
from app.modules.users.repository import UserRepository
from app.utils.bcrypt_util import BcryptUtil
from app.utils.email_util import EmailUtil
from app.utils.otp_util import OtpUtil


class UserService:
    RESTRICTED_ROLE_NAMES = {"SUPER_ADMIN", "COMPANY_ADMIN"}

    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        auth_repository: AuthRepository,
        email_util: EmailUtil,
        otp_util: OtpUtil,
        password_reset_otp_expire_minutes: int,
    ):
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.auth_repository = auth_repository
        self.email_util = email_util
        self.otp_util = otp_util
        self.password_reset_otp_expire_minutes = password_reset_otp_expire_minutes

    @staticmethod
    def _normalize_role_name(role) -> str | None:
        if not role:
            return None
        return role.name.strip().upper()

    @staticmethod
    def _build_role_response(role):
        if not role:
            return None

        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_system_role": role.is_system_role,
            "is_active": role.is_active,
        }

    @classmethod
    def _build_user_response(cls, user):
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "company_id": user.company_id,
            "is_active": user.is_active,
            "is_super_admin": user.is_super_admin,
            "role": cls._build_role_response(user.role),
        }

    @staticmethod
    def _get_actor_company_id(auth_context: AuthContext) -> uuid.UUID:
        if auth_context.company_id is None:
            raise AuthorizationException(
                message="You are not assigned to a company.",
                code="company_assignment_required",
            )
        return auth_context.company_id

    def _get_role_by_id(self, role_id: uuid.UUID):
        role = self.role_repository.get_role_by_id(role_id)
        if not role:
            raise NotFoundException(
                message="Role not found.",
                code="role_not_found",
            )
        if not role.is_active:
            raise BadRequestException(
                message="The selected role is inactive.",
                code="role_inactive",
            )
        return role

    def _get_company_admin_role(self):
        role = self.role_repository.get_role_by_name("COMPANY_ADMIN")
        if not role:
            raise NotFoundException(
                message="Company admin role not found.",
                code="role_not_found",
            )
        if not role.is_active:
            raise BadRequestException(
                message="Company admin role is inactive.",
                code="role_inactive",
            )
        return role

    def _resolve_target_company_id(
        self,
        auth_context: AuthContext,
        company_id: uuid.UUID | None,
    ) -> uuid.UUID | None:
        if auth_context.is_super_admin:
            return company_id

        actor_company_id = self._get_actor_company_id(auth_context)
        if company_id is not None and company_id != actor_company_id:
            raise AuthorizationException(
                message="You are not allowed to create users outside your company.",
                code="cross_company_user_creation_forbidden",
            )

        return actor_company_id

    def _ensure_assignable_role(self, role, *, action: str) -> None:
        role_name = self._normalize_role_name(role)
        if role_name in self.RESTRICTED_ROLE_NAMES:
            raise AuthorizationException(
                message=f"You are not allowed to {action} users with this role.",
                code="restricted_role_assignment",
            )

    def _create_invited_user_record(
        self,
        *,
        name: str,
        email: str,
        role_id: uuid.UUID,
        company_id: uuid.UUID | None,
        is_super_admin: bool = False,
    ):
        existing_user = self.user_repository.get_user_by_email(email)
        if existing_user:
            raise ConflictException(
                message="A user with this email already exists.",
                code="user_already_exists",
            )

        temporary_password = secrets.token_urlsafe(32)
        hashed_password = BcryptUtil.hash_password(temporary_password)
        return self.user_repository.create_user(
            name=name,
            email=email,
            hashed_password=hashed_password,
            is_active=False,
            is_super_admin=is_super_admin,
            role_id=role_id,
            company_id=company_id,
        )

    def send_account_setup_otp(self, user) -> None:
        otp_code = self.otp_util.generate_otp()
        otp_code_hash = self.otp_util.hash_otp(otp_code)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=self.password_reset_otp_expire_minutes
        )

        self.auth_repository.invalidate_password_reset_otps(user.id)
        password_reset_otp = self.auth_repository.create_password_reset_otp(
            user_id=user.id,
            otp_code_hash=otp_code_hash,
            expires_at=expires_at,
        )

        try:
            self.email_util.send_account_setup_otp(
                recipient_email=user.email,
                recipient_name=user.name,
                otp_code=otp_code,
                expires_in_minutes=self.password_reset_otp_expire_minutes,
            )
        except Exception as exc:
            self.auth_repository.mark_password_reset_otp_used(password_reset_otp.id)
            raise AppException(
                message="The account setup email could not be sent right now.",
                code="account_setup_email_failed",
            ) from exc

    def _create_invited_user(
        self,
        *,
        name: str,
        email: str,
        role_id: uuid.UUID,
        company_id: uuid.UUID | None,
        is_super_admin: bool = False,
        send_invite: bool = True,
    ):
        user = self._create_invited_user_record(
            name=name,
            email=email,
            role_id=role_id,
            company_id=company_id,
            is_super_admin=is_super_admin,
        )
        if send_invite:
            self.send_account_setup_otp(user)
        return user

    def create_company_admin(
        self,
        *,
        company_id: uuid.UUID,
        name: str,
        email: str,
        send_invite: bool = True,
    ):
        company_admin_role = self._get_company_admin_role()
        return self._create_invited_user(
            name=name,
            email=email,
            role_id=company_admin_role.id,
            company_id=company_id,
            send_invite=send_invite,
        )

    def create_user(
        self,
        auth_context: AuthContext,
        name: str,
        email: str,
        role_id: uuid.UUID,
        company_id: uuid.UUID | None = None,
    ):
        role = self._get_role_by_id(role_id)
        self._ensure_assignable_role(role, action="create")
        target_company_id = self._resolve_target_company_id(auth_context, company_id)

        return self._create_invited_user(
            name=name,
            email=email,
            role_id=role.id,
            company_id=target_company_id,
        )

    def update_user(
        self,
        auth_context: AuthContext,
        user_id: uuid.UUID,
        name: str | None = None,
        email: str | None = None,
        role_id: uuid.UUID | None = None,
        is_active: bool | None = None,
    ):
        actor_company_id = self._get_actor_company_id(auth_context)
        user = self.user_repository.get_user_by_id(user_id, company_id=actor_company_id)
        if not user:
            raise NotFoundException(
                message="User not found.",
                code="user_not_found",
            )

        self._ensure_assignable_role(user.role, action="manage")

        if email and email != user.email:
            existing_user = self.user_repository.get_user_by_email(email)
            if existing_user and existing_user.id != user_id:
                raise ConflictException(
                    message="A user with this email already exists.",
                    code="user_already_exists",
                )

        target_role_id = role_id
        if role_id is not None:
            role = self._get_role_by_id(role_id)
            self._ensure_assignable_role(role, action="assign")
            target_role_id = role.id

        return self.user_repository.update_user(
            user_id=user_id,
            name=name,
            email=email,
            role_id=target_role_id,
            is_active=is_active,
        )

    def get_all_users(self, auth_context: AuthContext):
        actor_company_id = self._get_actor_company_id(auth_context)
        users = self.user_repository.get_all_users(company_id=actor_company_id)
        return [self._build_user_response(user) for user in users]

    def get_user_by_id(self, auth_context: AuthContext, user_id: uuid.UUID):
        actor_company_id = self._get_actor_company_id(auth_context)
        user = self.user_repository.get_user_by_id(user_id, company_id=actor_company_id)
        if not user:
            raise NotFoundException(
                message="User not found.",
                code="user_not_found",
            )

        return self._build_user_response(user)
