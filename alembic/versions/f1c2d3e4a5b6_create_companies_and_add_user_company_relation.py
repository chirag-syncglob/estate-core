"""create companies and add user company relation

Revision ID: f1c2d3e4a5b6
Revises: c4f6b8a2d9e7
Create Date: 2026-04-01 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f1c2d3e4a5b6"
down_revision: Union[str, Sequence[str], None] = "c4f6b8a2d9e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "companies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("admin_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_companies_id"), "companies", ["id"], unique=False)
    op.create_index(op.f("ix_companies_admin_id"), "companies", ["admin_id"], unique=False)
    op.create_index(op.f("ix_companies_name"), "companies", ["name"], unique=True)

    op.add_column("users", sa.Column("company_id", sa.UUID(), nullable=True))
    op.create_index(op.f("ix_users_company_id"), "users", ["company_id"], unique=False)

    op.create_foreign_key(
        "fk_users_company_id_companies",
        "users",
        "companies",
        ["company_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_companies_admin_id_users",
        "companies",
        "users",
        ["admin_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_companies_admin_id_users", "companies", type_="foreignkey")
    op.drop_constraint("fk_users_company_id_companies", "users", type_="foreignkey")

    op.drop_index(op.f("ix_users_company_id"), table_name="users")
    op.drop_column("users", "company_id")

    op.drop_index(op.f("ix_companies_name"), table_name="companies")
    op.drop_index(op.f("ix_companies_admin_id"), table_name="companies")
    op.drop_index(op.f("ix_companies_id"), table_name="companies")
    op.drop_table("companies")
