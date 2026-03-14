"""Add telegram broadcast image presets.

Revision ID: 022
Revises: 021
Create Date: 2026-02-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "022"
down_revision: Union[str, None] = "021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "telegram_broadcast_image_presets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("alias", sa.String(length=120), nullable=False),
        sa.Column("image_path", sa.String(length=500), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("team_members.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_index(
        "idx_telegram_broadcast_image_presets_active_sort",
        "telegram_broadcast_image_presets",
        ["is_active", "sort_order", "created_at"],
        unique=False,
    )
    op.create_index(
        "uq_telegram_broadcast_image_presets_alias_lower",
        "telegram_broadcast_image_presets",
        [sa.text("lower(alias)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_telegram_broadcast_image_presets_alias_lower",
        table_name="telegram_broadcast_image_presets",
    )
    op.drop_index(
        "idx_telegram_broadcast_image_presets_active_sort",
        table_name="telegram_broadcast_image_presets",
    )
    op.drop_table("telegram_broadcast_image_presets")
