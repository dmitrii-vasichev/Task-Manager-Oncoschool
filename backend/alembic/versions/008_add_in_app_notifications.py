"""Add in-app notifications table.

Revision ID: 008
Revises: 007
Create Date: 2026-02-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "in_app_notifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "recipient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("team_members.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("team_members.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("action_url", sa.String(300), nullable=True),
        sa.Column("task_short_id", sa.Integer(), nullable=True),
        sa.Column("dedupe_key", sa.String(200), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("recipient_id", "dedupe_key"),
    )
    op.create_index(
        "idx_inapp_notifications_recipient_created",
        "in_app_notifications",
        ["recipient_id", "created_at"],
    )
    op.create_index(
        "idx_inapp_notifications_recipient_unread",
        "in_app_notifications",
        ["recipient_id", "is_read", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_inapp_notifications_recipient_unread", table_name="in_app_notifications")
    op.drop_index("idx_inapp_notifications_recipient_created", table_name="in_app_notifications")
    op.drop_table("in_app_notifications")
