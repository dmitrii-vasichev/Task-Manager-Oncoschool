"""Add digest sections order to reminder settings.

Revision ID: 023
Revises: 022
Create Date: 2026-02-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "023"
down_revision: Union[str, None] = "022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reminder_settings",
        sa.Column(
            "digest_sections_order",
            sa.ARRAY(sa.String()),
            nullable=False,
            server_default='{"overdue","upcoming","in_progress","new"}',
        ),
    )


def downgrade() -> None:
    op.drop_column("reminder_settings", "digest_sections_order")
