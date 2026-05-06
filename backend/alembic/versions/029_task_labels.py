"""Add task labels

Revision ID: 029
Revises: 028
Create Date: 2026-05-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "029"
down_revision: Union[str, None] = "028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "task_labels",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("color", sa.String(30), nullable=False),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("team_members.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_task_labels_slug"),
    )
    op.create_index("idx_task_labels_is_archived", "task_labels", ["is_archived"])
    op.create_index("idx_task_labels_created_at", "task_labels", ["created_at"])

    op.create_table(
        "task_label_links",
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "label_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("task_labels.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_task_label_links_label_id", "task_label_links", ["label_id"])
    op.create_index("idx_task_label_links_task_id", "task_label_links", ["task_id"])


def downgrade() -> None:
    op.drop_index("idx_task_label_links_task_id", table_name="task_label_links")
    op.drop_index("idx_task_label_links_label_id", table_name="task_label_links")
    op.drop_table("task_label_links")
    op.drop_index("idx_task_labels_created_at", table_name="task_labels")
    op.drop_index("idx_task_labels_is_archived", table_name="task_labels")
    op.drop_table("task_labels")
