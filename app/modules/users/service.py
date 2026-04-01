from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from app.core.exceptions import AppException, ConflictException, NotFoundException
from app.modules.auth.repository import AuthRepository
from app.modules.users.repository import UserRepository
from app.utils.bcrypt_util import BcryptUtil
from app.utils.email_util import EmailUtil
from app.utils.otp_util import OtpUtil


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        auth_repository: AuthRepository,
        email_util: EmailUtil,
        otp_util: OtpUtil,
        password_reset_otp_expire_minutes: int,
    ):
        self.user_repository = user_repository
        self.auth_repository = auth_repository
        self.email_util = email_util
        self.otp_util = otp_util
        self.password_reset_otp_expire_minutes = password_reset_otp_expire_minutes

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
            "is_active": user.is_active,
            "is_super_admin": user.is_super_admin,
            "role": cls._build_role_response(user.role),
        }

    def _send_account_setup_otp(self, user) -> None:
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
                message="User was created, but the account setup email could not be sent right now.",
                code="account_setup_email_failed",
            ) from exc

    def create_user(
        self,
        name: str,
        email: str,
        role_id: uuid.UUID | None = None,
        is_super_admin: bool = False,
    ):
        user = self.user_repository.get_user_by_email(email)
        if user:
            raise ConflictException(
                message="A user with this email already exists.",
                code="user_already_exists",
            )

        temporary_password = secrets.token_urlsafe(32)
        hashed_password = BcryptUtil.hash_password(temporary_password)
        created_user = self.user_repository.create_user(
            name=name,
            email=email,
            hashed_password=hashed_password,
            is_active=False,
            is_super_admin=is_super_admin,
            role_id=role_id,
        )
        self._send_account_setup_otp(created_user)
        return created_user

    def update_user(
        self,
        user_id: uuid.UUID,
        name: str | None = None,
        email: str | None = None,
        is_super_admin: bool | None = None,
        role_id: uuid.UUID | None = None,
        is_active: bool | None = None,
    ):
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            raise NotFoundException(
                message="User not found.",
                code="user_not_found",
            )

        if email and email != user.email:
            existing_user = self.user_repository.get_user_by_email(email)
            if existing_user and existing_user.id != user_id:
                raise ConflictException(
                    message="A user with this email already exists.",
                    code="user_already_exists",
                )

        return self.user_repository.update_user(
            user_id=user_id,
            name=name,
            email=email,
            is_super_admin=is_super_admin,
            role_id=role_id,
            is_active=is_active,
        )

    def get_all_users(self):
        users = self.user_repository.get_all_users()
        return [self._build_user_response(user) for user in users]

    def get_user_by_id(self, user_id: uuid.UUID):
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            raise NotFoundException(
                message="User not found.",
                code="user_not_found",
            )

        return self._build_user_response(user)
