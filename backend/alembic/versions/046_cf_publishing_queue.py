"""Add Content Factory publishing queue.

Revision ID: 046_cf_publishing_queue
Revises: 045_cf_pub_variants
Create Date: 2026-05-15 11:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "046_cf_publishing_queue"
down_revision: Union[str, None] = "045_cf_pub_variants"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cf_publishing_queue_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("publication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="queued", nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requested_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("manual_fallback_reason", sa.Text(), nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "provider_response",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["publication_id"],
            ["cf_publication.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["platform_id"], ["cf_platform.id"]),
        sa.ForeignKeyConstraint(["requested_by_id"], ["team_members.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cf_publishing_queue_status_schedule",
        "cf_publishing_queue_item",
        ["status", "scheduled_for"],
    )
    op.create_index(
        "ix_cf_publishing_queue_publication",
        "cf_publishing_queue_item",
        ["publication_id"],
    )
    op.create_index(
        "ix_cf_publishing_queue_platform",
        "cf_publishing_queue_item",
        ["platform_id"],
    )
    op.create_index(
        "ix_cf_publishing_queue_next_retry",
        "cf_publishing_queue_item",
        ["next_retry_at"],
    )

    op.create_table(
        "cf_publishing_queue_event",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("queue_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("publication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["queue_item_id"],
            ["cf_publishing_queue_item.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["publication_id"],
            ["cf_publication.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["team_members.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cf_publishing_queue_event_item_created",
        "cf_publishing_queue_event",
        ["queue_item_id", "created_at"],
    )
    op.create_index(
        "ix_cf_publishing_queue_event_publication_created",
        "cf_publishing_queue_event",
        ["publication_id", "created_at"],
    )
    op.create_index(
        "ix_cf_publishing_queue_event_type",
        "cf_publishing_queue_event",
        ["event_type"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_cf_publishing_queue_event_type",
        table_name="cf_publishing_queue_event",
    )
    op.drop_index(
        "ix_cf_publishing_queue_event_publication_created",
        table_name="cf_publishing_queue_event",
    )
    op.drop_index(
        "ix_cf_publishing_queue_event_item_created",
        table_name="cf_publishing_queue_event",
    )
    op.drop_table("cf_publishing_queue_event")
    op.drop_index(
        "ix_cf_publishing_queue_next_retry",
        table_name="cf_publishing_queue_item",
    )
    op.drop_index(
        "ix_cf_publishing_queue_platform",
        table_name="cf_publishing_queue_item",
    )
    op.drop_index(
        "ix_cf_publishing_queue_publication",
        table_name="cf_publishing_queue_item",
    )
    op.drop_index(
        "ix_cf_publishing_queue_status_schedule",
        table_name="cf_publishing_queue_item",
    )
    op.drop_table("cf_publishing_queue_item")
