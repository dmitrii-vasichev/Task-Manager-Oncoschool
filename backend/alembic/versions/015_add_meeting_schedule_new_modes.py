"""Add one_time/on_demand schedule support

Revision ID: 015
Revises: 014
Create Date: 2026-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "meeting_schedules",
        sa.Column("one_time_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "meeting_schedules",
        sa.Column("next_occurrence_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("meeting_schedules", "next_occurrence_at")
    op.drop_column("meeting_schedules", "one_time_date")
