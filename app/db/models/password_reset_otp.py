import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PasswordResetOTP(Base):
    __tablename__ = "password_reset_otps"
    __table_args__ = (
        Index(
            "ix_password_reset_otps_user_id_otp_code_hash",
            "user_id",
            "otp_code_hash",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    otp_code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
