"""Add reminder zoom block configuration to meeting schedules.

Revision ID: 011
Revises: 010
Create Date: 2026-02-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "meeting_schedules",
        sa.Column(
            "reminder_include_zoom_link",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "meeting_schedules",
        sa.Column(
            "reminder_zoom_missing_behavior",
            sa.String(length=20),
            nullable=False,
            server_default="hide",
        ),
    )
    op.add_column(
        "meeting_schedules",
        sa.Column("reminder_zoom_missing_text", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("meeting_schedules", "reminder_zoom_missing_text")
    op.drop_column("meeting_schedules", "reminder_zoom_missing_behavior")
    op.drop_column("meeting_schedules", "reminder_include_zoom_link")
