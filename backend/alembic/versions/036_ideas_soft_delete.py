"""Add soft delete fields to ideas.

Revision ID: 036_ideas_soft_delete
Revises: 035_ideas_module
Create Date: 2026-05-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "036_ideas_soft_delete"
down_revision: Union[str, None] = "035_ideas_module"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ideas", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.add_column(
        "ideas",
        sa.Column("deleted_by_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_ideas_deleted_by_id_team_members",
        "ideas",
        "team_members",
        ["deleted_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_ideas_deleted_at", "ideas", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("idx_ideas_deleted_at", table_name="ideas")
    op.drop_constraint("fk_ideas_deleted_by_id_team_members", "ideas", type_="foreignkey")
    op.drop_column("ideas", "deleted_by_id")
    op.drop_column("ideas", "deleted_at")
