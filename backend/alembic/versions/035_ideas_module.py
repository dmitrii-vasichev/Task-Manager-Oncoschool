"""Add ideas module tables.

Revision ID: 035_ideas_module
Revises: 034_meeting_board_focus_labels
Create Date: 2026-05-12
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "035_ideas_module"
down_revision: Union[str, None] = "034_meeting_board_focus_labels"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ideas",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), server_default="new", nullable=False),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("team_members.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "review_owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("team_members.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("decision_comment", sa.Text(), nullable=True),
        sa.Column(
            "decision_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("team_members.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("decision_at", sa.DateTime(), nullable=True),
        sa.Column("deferred_until", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_ideas_status", "ideas", ["status"])
    op.create_index("idx_ideas_author_id", "ideas", ["author_id"])
    op.create_index("idx_ideas_review_owner_id", "ideas", ["review_owner_id"])
    op.create_index("idx_ideas_created_at", "ideas", ["created_at"])

    op.create_table(
        "idea_departments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "idea_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ideas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("departments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("team_members.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(30),
            server_default="not_started",
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("team_members.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "idea_id",
            "department_id",
            name="uq_idea_departments_idea_department",
        ),
    )
    op.create_index("idx_idea_departments_idea_id", "idea_departments", ["idea_id"])
    op.create_index(
        "idx_idea_departments_department_id",
        "idea_departments",
        ["department_id"],
    )
    op.create_index("idx_idea_departments_owner_id", "idea_departments", ["owner_id"])
    op.create_index("idx_idea_departments_status", "idea_departments", ["status"])

    op.create_table(
        "idea_tasks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "idea_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ideas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "idea_department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("idea_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("team_members.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("task_id", name="uq_idea_tasks_task_id"),
    )
    op.create_index("idx_idea_tasks_idea_id", "idea_tasks", ["idea_id"])
    op.create_index(
        "idx_idea_tasks_idea_department_id",
        "idea_tasks",
        ["idea_department_id"],
    )
    op.create_index("idx_idea_tasks_task_id", "idea_tasks", ["task_id"])

    op.create_table(
        "idea_comments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "idea_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ideas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("team_members.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_idea_comments_idea_id", "idea_comments", ["idea_id"])
    op.create_index("idx_idea_comments_created_at", "idea_comments", ["created_at"])

    op.create_table(
        "idea_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "idea_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ideas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("team_members.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("payload", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_idea_events_idea_id", "idea_events", ["idea_id"])
    op.create_index("idx_idea_events_created_at", "idea_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_idea_events_created_at", table_name="idea_events")
    op.drop_index("idx_idea_events_idea_id", table_name="idea_events")
    op.drop_table("idea_events")

    op.drop_index("idx_idea_comments_created_at", table_name="idea_comments")
    op.drop_index("idx_idea_comments_idea_id", table_name="idea_comments")
    op.drop_table("idea_comments")

    op.drop_index("idx_idea_tasks_task_id", table_name="idea_tasks")
    op.drop_index("idx_idea_tasks_idea_department_id", table_name="idea_tasks")
    op.drop_index("idx_idea_tasks_idea_id", table_name="idea_tasks")
    op.drop_table("idea_tasks")

    op.drop_index("idx_idea_departments_status", table_name="idea_departments")
    op.drop_index("idx_idea_departments_owner_id", table_name="idea_departments")
    op.drop_index("idx_idea_departments_department_id", table_name="idea_departments")
    op.drop_index("idx_idea_departments_idea_id", table_name="idea_departments")
    op.drop_table("idea_departments")

    op.drop_index("idx_ideas_created_at", table_name="ideas")
    op.drop_index("idx_ideas_review_owner_id", table_name="ideas")
    op.drop_index("idx_ideas_author_id", table_name="ideas")
    op.drop_index("idx_ideas_status", table_name="ideas")
    op.drop_table("ideas")
