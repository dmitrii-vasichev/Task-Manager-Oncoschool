"""Add per-offset reminder templates for meeting schedules.

Revision ID: 017
Revises: 016
Create Date: 2026-02-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "meeting_schedules",
        sa.Column(
            "reminder_texts_by_offset",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )

    # Backfill primary reminder text into currently leading offset template.
    op.execute(
        """
        UPDATE meeting_schedules
        SET reminder_texts_by_offset = CASE
            WHEN reminder_text IS NULL OR btrim(reminder_text) = '' THEN '{}'::jsonb
            ELSE jsonb_build_object(
                COALESCE(
                    reminder_offsets_minutes[1]::text,
                    LEAST(GREATEST(COALESCE(reminder_minutes_before, 60), 0), 10080)::text
                ),
                reminder_text
            )
        END
        WHERE reminder_texts_by_offset IS NULL
           OR reminder_texts_by_offset = '{}'::jsonb
        """
    )


def downgrade() -> None:
    op.drop_column("meeting_schedules", "reminder_texts_by_offset")
