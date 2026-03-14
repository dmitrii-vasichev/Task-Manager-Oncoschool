"""Add last_triggered_date to meeting_schedules.

Revision ID: 005
Revises: 004
Create Date: 2026-02-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "meeting_schedules",
        sa.Column("last_triggered_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("meeting_schedules", "last_triggered_date")
