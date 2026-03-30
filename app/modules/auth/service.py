from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.core.exceptions import AppException, AuthenticationException, BadRequestException
from app.modules.auth.repository import AuthRepository
from app.utils.bcrypt_util import BcryptUtil
from app.utils.email_util import EmailUtil
from app.utils.jwt_util import JwtUtil
from app.utils.otp_util import OtpUtil


class AuthService:
    def __init__(
        self,
        auth_repository: AuthRepository,
        jwt_util: JwtUtil,
        email_util: EmailUtil,
        otp_util: OtpUtil,
        password_reset_otp_expire_minutes: int,
    ):
        self.auth_repository = auth_repository
        self.jwt_util = jwt_util
        self.email_util = email_util
        self.otp_util = otp_util
        self.password_reset_otp_expire_minutes = password_reset_otp_expire_minutes

    @staticmethod
    def _build_user_response(user):
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_active": user.is_active,
            "is_super_admin": user.is_super_admin,
        }

    def login(self, email: str, password: str):
        user = self.auth_repository.get_user_by_email(email)
        if not user:
            raise AuthenticationException(
                message="Invalid email or password.",
                code="invalid_credentials",
            )

        is_valid_password = BcryptUtil.verify_password(password, user.password_hash)
        if not is_valid_password:
            raise AuthenticationException(
                message="Invalid email or password.",
                code="invalid_credentials",
            )

        token_pair = self.jwt_util.create_token_pair(
            subject=str(user.id),
            extra_claims={"email": user.email, "is_super_admin": user.is_super_admin},
        )

        return {
            "user": self._build_user_response(user),
            "tokens": token_pair,
        }

    def register(self, username: str, email: str, password: str):
        hashed_password = BcryptUtil.hash_password(password)
        user = self.auth_repository.create_user(
            name=username,
            email=email,
            hashed_password=hashed_password,
        )
        token_pair = self.jwt_util.create_token_pair(
            subject=str(user.id),
            extra_claims={"email": user.email, "is_super_admin": user.is_super_admin},
        )

        return {
            "message": "Registration successful",
            "user": self._build_user_response(user),
            "tokens": token_pair,
        }

    def refresh_tokens(self, refresh_token: str):
        try:
            payload = self.jwt_util.verify_refresh_token(refresh_token)
            user_id = uuid.UUID(str(payload["sub"]))
        except (KeyError, ValueError) as exc:
            raise AuthenticationException(
                message="Invalid or expired refresh token.",
                code="invalid_refresh_token",
            ) from exc

        user = self.auth_repository.get_user_by_id(user_id)
        if not user:
            raise AuthenticationException(
                message="Invalid or expired refresh token.",
                code="invalid_refresh_token",
            )

        token_pair = self.jwt_util.create_token_pair(
            subject=str(user.id),
            extra_claims={"email": user.email, "is_super_admin": user.is_super_admin},
        )

        return {
            "user": self._build_user_response(user),
            "tokens": token_pair,
        }

    def get_current_user(self, user_id: uuid.UUID):
        user = self.auth_repository.get_user_by_id(user_id)
        if not user:
            raise AuthenticationException(
                message="User not found.",
                code="user_not_found",
            )

        return self._build_user_response(user)

    def forgot_password(self, email: str):
        user = self.auth_repository.get_user_by_email(email)
        response = {
            "message": "If an account with that email exists, an OTP has been sent.",
        }
        if not user:
            return response

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
            self.email_util.send_password_reset_otp(
                recipient_email=user.email,
                recipient_name=user.name,
                otp_code=otp_code,
                expires_in_minutes=self.password_reset_otp_expire_minutes,
            )
        except Exception as exc:
            self.auth_repository.mark_password_reset_otp_used(password_reset_otp.id)
            raise AppException(
                message="Unable to send password reset OTP right now.",
                code="password_reset_otp_delivery_failed",
            ) from exc

        return response

    def reset_password(self, email: str, otp: str, new_password: str):
        user = self.auth_repository.get_user_by_email(email)
        if not user:
            raise BadRequestException(
                message="Invalid or expired OTP.",
                code="invalid_reset_otp",
            )

        otp_code_hash = self.otp_util.hash_otp(otp)
        password_reset_otp = self.auth_repository.get_valid_password_reset_otp(
            user_id=user.id,
            otp_code_hash=otp_code_hash,
        )
        if not password_reset_otp:
            raise BadRequestException(
                message="Invalid or expired OTP.",
                code="invalid_reset_otp",
            )

        hashed_password = BcryptUtil.hash_password(new_password)
        updated_user = self.auth_repository.reset_user_password(
            user_id=user.id,
            otp_id=password_reset_otp.id,
            hashed_password=hashed_password,
        )

        return {
            "message": "Password reset successful",
            "user": self._build_user_response(updated_user),
        }
