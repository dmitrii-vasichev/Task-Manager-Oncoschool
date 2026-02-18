"""Add next_occurrence_skip and next_occurrence_time_override to meeting_schedules.

Revision ID: 006
Revises: 005
Create Date: 2026-02-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "meeting_schedules",
        sa.Column("next_occurrence_skip", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "meeting_schedules",
        sa.Column("next_occurrence_time_override", sa.Time(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("meeting_schedules", "next_occurrence_time_override")
    op.drop_column("meeting_schedules", "next_occurrence_skip")
