"""create password reset otps table

Revision ID: 5b6b2c7c9f40
Revises: bdcaf57212fe
Create Date: 2026-03-30 12:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5b6b2c7c9f40"
down_revision: Union[str, Sequence[str], None] = "bdcaf57212fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "password_reset_otps",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("otp_code_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_password_reset_otps_user_id_otp_code_hash",
        "password_reset_otps",
        ["user_id", "otp_code_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_password_reset_otps_user_id"),
        "password_reset_otps",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_password_reset_otps_user_id"), table_name="password_reset_otps")
    op.drop_index("ix_password_reset_otps_user_id_otp_code_hash", table_name="password_reset_otps")
    op.drop_table("password_reset_otps")
