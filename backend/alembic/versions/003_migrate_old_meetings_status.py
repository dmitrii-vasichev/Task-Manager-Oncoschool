"""Migrate old meetings: set status='completed' for existing records.

Old meetings (created before the meetings overhaul) have raw_summary filled
and were created via /summary parsing — they are definitely completed.
The status column was added in 002 with server_default='scheduled', so
existing rows got status='scheduled' which is incorrect for historical data.

Revision ID: 003
Revises: 002
Create Date: 2026-02-12

"""
from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # All meetings that have parsed_summary are definitely completed
    op.execute(
        "UPDATE meetings SET status = 'completed' "
        "WHERE parsed_summary IS NOT NULL AND status != 'completed'"
    )
    # Remaining old meetings (with raw_summary but no parsed_summary) are also completed
    op.execute(
        "UPDATE meetings SET status = 'completed' "
        "WHERE raw_summary IS NOT NULL AND status = 'scheduled'"
    )


def downgrade() -> None:
    # Cannot reliably revert — we don't know which were originally 'scheduled'
    pass
