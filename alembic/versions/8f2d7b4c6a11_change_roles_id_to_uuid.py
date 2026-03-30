"""change roles id to uuid

Revision ID: 8f2d7b4c6a11
Revises: e3e4d0b9c1a1
Create Date: 2026-03-30 13:40:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8f2d7b4c6a11"
down_revision: Union[str, Sequence[str], None] = "e3e4d0b9c1a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_roles_id_type(bind) -> str | None:
    return bind.execute(
        sa.text(
            """
            select udt_name
            from information_schema.columns
            where table_schema = 'public'
              and table_name = 'roles'
              and column_name = 'id'
            """
        )
    ).scalar_one_or_none()


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    if _get_roles_id_type(bind) == "uuid":
        return

    roles_table = sa.table(
        "roles",
        sa.column("id", sa.Integer()),
        sa.column("id_uuid", sa.UUID()),
    )

    op.add_column("roles", sa.Column("id_uuid", sa.UUID(), nullable=True))

    existing_role_ids = bind.execute(sa.select(roles_table.c.id)).scalars().all()
    for role_id in existing_role_ids:
        bind.execute(
            sa.update(roles_table)
            .where(roles_table.c.id == role_id)
            .values(id_uuid=uuid.uuid4())
        )

    op.alter_column("roles", "id_uuid", nullable=False)

    inspector = sa.inspect(bind)
    index_names = {index["name"] for index in inspector.get_indexes("roles")}
    if op.f("ix_roles_id") in index_names:
        op.drop_index(op.f("ix_roles_id"), table_name="roles")

    primary_key_name = inspector.get_pk_constraint("roles").get("name")
    if primary_key_name:
        op.drop_constraint(primary_key_name, "roles", type_="primary")

    op.drop_column("roles", "id")
    op.alter_column("roles", "id_uuid", new_column_name="id")
    op.create_primary_key("roles_pkey", "roles", ["id"])
    op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    if _get_roles_id_type(bind) == "int4":
        return

    op.add_column("roles", sa.Column("id_int", sa.Integer(), nullable=True))
    op.execute(sa.text("CREATE SEQUENCE IF NOT EXISTS roles_id_int_seq"))
    op.execute(sa.text("ALTER SEQUENCE roles_id_int_seq OWNED BY roles.id_int"))
    op.execute(
        sa.text(
            "ALTER TABLE roles ALTER COLUMN id_int SET DEFAULT nextval('roles_id_int_seq')"
        )
    )
    op.execute(sa.text("UPDATE roles SET id_int = nextval('roles_id_int_seq') WHERE id_int IS NULL"))
    op.alter_column("roles", "id_int", nullable=False)

    inspector = sa.inspect(bind)
    index_names = {index["name"] for index in inspector.get_indexes("roles")}
    if op.f("ix_roles_id") in index_names:
        op.drop_index(op.f("ix_roles_id"), table_name="roles")

    primary_key_name = inspector.get_pk_constraint("roles").get("name")
    if primary_key_name:
        op.drop_constraint(primary_key_name, "roles", type_="primary")

    op.drop_column("roles", "id")
    op.alter_column("roles", "id_int", new_column_name="id")
    op.create_primary_key("roles_pkey", "roles", ["id"])
    op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)
