"""Add departments table, extend team_members, migrate roles.

Revision ID: 004
Revises: 003
Create Date: 2026-02-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create departments table
    op.create_table(
        "departments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("head_id", UUID(as_uuid=True), sa.ForeignKey("team_members.id"), nullable=True),
        sa.Column("sort_order", sa.Integer, server_default="0", nullable=False),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 2. Add new columns to team_members
    op.add_column("team_members", sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=True))
    op.add_column("team_members", sa.Column("position", sa.String(200), nullable=True))
    op.add_column("team_members", sa.Column("email", sa.String(255), nullable=True))
    op.add_column("team_members", sa.Column("birthday", sa.Date, nullable=True))
    op.add_column("team_members", sa.Column("avatar_url", sa.String(500), nullable=True))

    # 3. Migrate roles: moderator → admin
    op.execute("UPDATE team_members SET role = 'admin' WHERE role = 'moderator'")


def downgrade() -> None:
    # 1. Revert roles: admin → moderator
    op.execute("UPDATE team_members SET role = 'moderator' WHERE role = 'admin'")

    # 2. Drop new columns from team_members
    op.drop_column("team_members", "avatar_url")
    op.drop_column("team_members", "birthday")
    op.drop_column("team_members", "email")
    op.drop_column("team_members", "position")
    op.drop_column("team_members", "department_id")

    # 3. Drop departments table
    op.drop_table("departments")
