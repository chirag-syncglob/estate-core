from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, DatabaseException
from app.db.models import PasswordResetOTP, User


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def invalidate_password_reset_otps(self, user_id: uuid.UUID):
        try:
            now = datetime.now(timezone.utc)
            otps = (
                self.db.query(PasswordResetOTP)
                .filter(
                    PasswordResetOTP.user_id == user_id,
                    PasswordResetOTP.used_at.is_(None),
                )
                .all()
            )
            for otp in otps:
                otp.used_at = now

            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(
                message="Unable to update password reset OTPs right now."
            ) from exc

    def create_password_reset_otp(
        self,
        user_id: uuid.UUID,
        otp_code_hash: str,
        expires_at: datetime,
    ):
        try:
            password_reset_otp = PasswordResetOTP(
                user_id=user_id,
                otp_code_hash=otp_code_hash,
                expires_at=expires_at,
            )
            self.db.add(password_reset_otp)
            self.db.commit()
            self.db.refresh(password_reset_otp)
            return password_reset_otp
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(
                message="Unable to create password reset OTP right now."
            ) from exc

    def get_valid_password_reset_otp(self, user_id: uuid.UUID, otp_code_hash: str):
        try:
            now = datetime.now(timezone.utc)
            return (
                self.db.query(PasswordResetOTP)
                .filter(
                    PasswordResetOTP.user_id == user_id,
                    PasswordResetOTP.otp_code_hash == otp_code_hash,
                    PasswordResetOTP.used_at.is_(None),
                    PasswordResetOTP.expires_at >= now,
                )
                .order_by(PasswordResetOTP.created_at.desc())
                .first()
            )
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(
                message="Unable to load password reset OTP right now."
            ) from exc

    def mark_password_reset_otp_used(self, otp_id: uuid.UUID):
        try:
            otp = self.db.query(PasswordResetOTP).filter(PasswordResetOTP.id == otp_id).first()
            if not otp:
                raise ConflictException(
                    message="Password reset OTP not found.",
                    code="password_reset_otp_not_found",
                )

            otp.used_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(otp)
            return otp
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(
                message="Unable to update password reset OTP right now."
            ) from exc

    def reset_user_password(self, user_id: uuid.UUID, otp_id: uuid.UUID, hashed_password: str):
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ConflictException(
                    message="User not found.",
                    code="user_not_found",
                )

            otp = (
                self.db.query(PasswordResetOTP)
                .filter(
                    PasswordResetOTP.id == otp_id,
                    PasswordResetOTP.user_id == user_id,
                )
                .first()
            )
            if not otp:
                raise ConflictException(
                    message="Password reset OTP not found.",
                    code="password_reset_otp_not_found",
                )

            now = datetime.now(timezone.utc)
            user.password_hash = hashed_password
            user.is_active = True
            otp.used_at = now

            other_otps = (
                self.db.query(PasswordResetOTP)
                .filter(
                    PasswordResetOTP.user_id == user_id,
                    PasswordResetOTP.id != otp_id,
                    PasswordResetOTP.used_at.is_(None),
                )
                .all()
            )
            for other_otp in other_otps:
                other_otp.used_at = now

            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException(
                message="Unable to reset the password right now.",
                code="password_reset_conflict",
            ) from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to reset the password right now.") from exc
