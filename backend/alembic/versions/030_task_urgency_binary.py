"""Convert task priority to binary urgency

Revision ID: 030
Revises: 029
Create Date: 2026-05-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "030"
down_revision: Union[str, None] = "029"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE tasks
        SET priority = CASE
            WHEN lower(coalesce(priority, '')) IN ('urgent', 'high') THEN 'urgent'
            ELSE 'normal'
        END
        """
    )
    op.alter_column(
        "tasks",
        "priority",
        existing_type=sa.String(length=20),
        server_default="normal",
        existing_nullable=False,
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE tasks
        SET priority = CASE
            WHEN priority = 'urgent' THEN 'urgent'
            ELSE 'medium'
        END
        """
    )
    op.alter_column(
        "tasks",
        "priority",
        existing_type=sa.String(length=20),
        server_default="medium",
        existing_nullable=False,
    )
