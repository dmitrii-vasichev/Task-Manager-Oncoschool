"""Add Content Factory guest story CRM table.

Revision ID: 042_content_factory_guest_story
Revises: 041
Create Date: 2026-05-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "042_content_factory_guest_story"
down_revision: Union[str, None] = "041"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cf_guest_story",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("contact_ref", sa.String(300), nullable=True),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("source", sa.String(30), nullable=False, server_default="manual"),
        sa.Column("source_notes", sa.Text(), nullable=True),
        sa.Column("story_brief", sa.Text(), nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="sourced"),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("team_members.id"),
            nullable=False,
        ),
        sa.Column("stage_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "nosology_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cf_nosology.id"),
            nullable=True,
        ),
        sa.Column(
            "bundle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cf_bundle.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "publication_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cf_publication.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("screening_notes", sa.Text(), nullable=True),
        sa.Column("medical_factcheck_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("consent_status", sa.String(30), nullable=False, server_default="not_started"),
        sa.Column("consent_version", sa.String(50), nullable=True),
        sa.Column("consent_signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "allowed_channels",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("anonymity_level", sa.String(30), nullable=False, server_default="full_name"),
        sa.Column(
            "sensitive_topics",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("legal_notes", sa.Text(), nullable=True),
        sa.Column("gift_status", sa.String(30), nullable=False, server_default="not_required"),
        sa.Column("follow_up_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cf_guest_story_status", "cf_guest_story", ["status"])
    op.create_index("ix_cf_guest_story_owner", "cf_guest_story", ["owner_id"])
    op.create_index("ix_cf_guest_story_bundle", "cf_guest_story", ["bundle_id"])
    op.create_index("ix_cf_guest_story_publication", "cf_guest_story", ["publication_id"])
    op.create_index("ix_cf_guest_story_stage_due", "cf_guest_story", ["stage_due_at"])


def downgrade() -> None:
    op.drop_index("ix_cf_guest_story_stage_due", table_name="cf_guest_story")
    op.drop_index("ix_cf_guest_story_publication", table_name="cf_guest_story")
    op.drop_index("ix_cf_guest_story_bundle", table_name="cf_guest_story")
    op.drop_index("ix_cf_guest_story_owner", table_name="cf_guest_story")
    op.drop_index("ix_cf_guest_story_status", table_name="cf_guest_story")
    op.drop_table("cf_guest_story")
