"""Add upcoming days setting to reminder settings.

Revision ID: 025
Revises: 024
Create Date: 2026-02-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "025"
down_revision: Union[str, None] = "024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reminder_settings",
        sa.Column("upcoming_days", sa.Integer(), nullable=False, server_default=sa.text("3")),
    )


def downgrade() -> None:
    op.drop_column("reminder_settings", "upcoming_days")
