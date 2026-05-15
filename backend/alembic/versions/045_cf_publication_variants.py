"""Add saved publication channel variants.

Revision ID: 045_cf_pub_variants
Revises: 044_cf_guest_event_threads
Create Date: 2026-05-15 10:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "045_cf_pub_variants"
down_revision: Union[str, None] = "044_cf_guest_event_threads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cf_publication_variant",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "publication_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("channel", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "source_version_number",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["publication_id"],
            ["cf_publication.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["updated_by_id"], ["team_members.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "publication_id",
            "channel",
            name="uq_cf_publication_variant_channel",
        ),
    )
    op.create_index(
        "ix_cf_publication_variant_publication",
        "cf_publication_variant",
        ["publication_id"],
    )
    op.create_index(
        "ix_cf_publication_variant_channel",
        "cf_publication_variant",
        ["channel"],
    )


def downgrade() -> None:
    op.drop_index("ix_cf_publication_variant_channel", table_name="cf_publication_variant")
    op.drop_index(
        "ix_cf_publication_variant_publication",
        table_name="cf_publication_variant",
    )
    op.drop_table("cf_publication_variant")
