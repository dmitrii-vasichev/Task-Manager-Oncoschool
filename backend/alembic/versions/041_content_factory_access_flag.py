"""Add has_content_factory_access flag to team_members.

Revision ID: 041_content_factory_access_flag
Revises: 040_content_factory_core
Create Date: 2026-05-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "041"
down_revision: Union[str, None] = "040_content_factory_core"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "team_members",
        sa.Column(
            "has_content_factory_access",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    # Admins implicitly get access via PermissionService; no data backfill needed.


def downgrade() -> None:
    op.drop_column("team_members", "has_content_factory_access")
