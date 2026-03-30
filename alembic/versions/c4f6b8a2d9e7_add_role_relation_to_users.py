"""add role relation to users

Revision ID: c4f6b8a2d9e7
Revises: 8f2d7b4c6a11
Create Date: 2026-03-30 14:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4f6b8a2d9e7"
down_revision: Union[str, Sequence[str], None] = "8f2d7b4c6a11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("role_id", sa.UUID(), nullable=True))
    op.create_index(op.f("ix_users_role_id"), "users", ["role_id"], unique=False)
    op.create_foreign_key(
        "fk_users_role_id_roles",
        "users",
        "roles",
        ["role_id"],
        ["id"],
        ondelete="SET NULL",
    )

    bind = op.get_bind()
    super_admin_role_id = bind.execute(
        sa.text("select id from roles where name = 'SUPER_ADMIN' limit 1")
    ).scalar_one_or_none()
    if super_admin_role_id is not None:
        bind.execute(
            sa.text(
                """
                update users
                set role_id = :role_id
                where is_super_admin = true
                  and role_id is null
                """
            ),
            {"role_id": super_admin_role_id},
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_users_role_id_roles", "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_role_id"), table_name="users")
    op.drop_column("users", "role_id")
