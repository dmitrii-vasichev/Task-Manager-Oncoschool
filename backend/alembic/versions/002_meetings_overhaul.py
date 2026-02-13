"""Meetings overhaul: meeting_schedules, telegram_notification_targets,
meetings new columns (zoom, schedule, transcript, status)

Revision ID: 002
Revises: 001
Create Date: 2026-02-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── meeting_schedules (NEW) ──
    op.create_table(
        "meeting_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("time_utc", sa.Time(), nullable=False),
        sa.Column("timezone", sa.String(50), server_default="Europe/Moscow"),
        sa.Column("duration_minutes", sa.Integer(), server_default="60"),
        sa.Column("recurrence", sa.String(30), server_default="weekly"),
        sa.Column("reminder_enabled", sa.Boolean(), server_default="true"),
        sa.Column("reminder_minutes_before", sa.Integer(), server_default="60"),
        sa.Column("reminder_text", sa.Text(), nullable=True),
        sa.Column("telegram_targets", postgresql.JSONB(), server_default="[]"),
        sa.Column("participant_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default="{}"),
        sa.Column("zoom_enabled", sa.Boolean(), server_default="true"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("team_members.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_meeting_schedules_active", "meeting_schedules", ["is_active", "day_of_week"])

    # ── telegram_notification_targets (NEW) ──
    op.create_table(
        "telegram_notification_targets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("thread_id", sa.Integer(), nullable=True),
        sa.Column("label", sa.String(200), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── ALTER meetings — add new columns ──
    op.add_column("meetings", sa.Column("schedule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("meeting_schedules.id"), nullable=True))
    op.add_column("meetings", sa.Column("zoom_meeting_id", sa.String(50), nullable=True))
    op.add_column("meetings", sa.Column("zoom_join_url", sa.Text(), nullable=True))
    op.add_column("meetings", sa.Column("zoom_recording_url", sa.Text(), nullable=True))
    op.add_column("meetings", sa.Column("transcript", sa.Text(), nullable=True))
    op.add_column("meetings", sa.Column("transcript_source", sa.String(20), nullable=True))
    op.add_column("meetings", sa.Column("status", sa.String(30), server_default="scheduled"))

    # Make raw_summary nullable (was NOT NULL)
    op.alter_column("meetings", "raw_summary", existing_type=sa.Text(), nullable=True)

    # Indexes
    op.create_index("idx_meetings_schedule", "meetings", ["schedule_id"])
    op.create_index("idx_meetings_status", "meetings", ["status"])
    op.create_index("idx_meetings_zoom", "meetings", ["zoom_meeting_id"])


def downgrade() -> None:
    op.drop_index("idx_meetings_zoom", table_name="meetings")
    op.drop_index("idx_meetings_status", table_name="meetings")
    op.drop_index("idx_meetings_schedule", table_name="meetings")

    op.alter_column("meetings", "raw_summary", existing_type=sa.Text(), nullable=False)

    op.drop_column("meetings", "status")
    op.drop_column("meetings", "transcript_source")
    op.drop_column("meetings", "transcript")
    op.drop_column("meetings", "zoom_recording_url")
    op.drop_column("meetings", "zoom_join_url")
    op.drop_column("meetings", "zoom_meeting_id")
    op.drop_column("meetings", "schedule_id")

    op.drop_table("telegram_notification_targets")
    op.drop_index("idx_meeting_schedules_active", table_name="meeting_schedules")
    op.drop_table("meeting_schedules")
