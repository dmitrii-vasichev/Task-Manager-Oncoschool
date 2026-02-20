"""Add extra department access mapping for team members.

Revision ID: 012
Revises: 011
Create Date: 2026-02-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "team_member_department_access",
        sa.Column(
            "member_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("team_members.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("departments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "granted_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("team_members.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("member_id", "department_id"),
    )
    op.create_index(
        "idx_team_member_department_access_department_id",
        "team_member_department_access",
        ["department_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_team_member_department_access_department_id",
        table_name="team_member_department_access",
    )
    op.drop_table("team_member_department_access")
