"""Migrate telegram_notification_targets.type (string) to types (ARRAY).

Merges duplicate rows with same (chat_id, thread_id) into a single row
with an array of types.

Revision ID: 028
Revises: 027
Create Date: 2026-03-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

revision: str = "028"
down_revision: Union[str, None] = "027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new 'types' column as ARRAY(String(50)), default empty array
    op.add_column(
        "telegram_notification_targets",
        sa.Column("types", ARRAY(sa.String(50)), server_default="{}", nullable=False),
    )

    # 2. Populate 'types' from existing 'type' column
    op.execute("""
        UPDATE telegram_notification_targets
        SET types = ARRAY[COALESCE(type, 'meeting')]
    """)

    # 3. Merge duplicates: for rows with same (chat_id, thread_id),
    #    keep the one with earliest created_at, aggregate types from all duplicates
    op.execute("""
        WITH ranked AS (
            SELECT id, chat_id, COALESCE(thread_id, 0) AS tid,
                   types,
                   ROW_NUMBER() OVER (
                       PARTITION BY chat_id, COALESCE(thread_id, 0)
                       ORDER BY created_at
                   ) AS rn
            FROM telegram_notification_targets
        ),
        merged_types AS (
            SELECT chat_id, tid,
                   ARRAY(SELECT DISTINCT unnest FROM (
                       SELECT unnest(types) FROM ranked r2
                       WHERE r2.chat_id = ranked.chat_id AND r2.tid = ranked.tid
                   ) sub) AS all_types
            FROM ranked
            WHERE rn = 1
            GROUP BY chat_id, tid
        ),
        keeper AS (
            SELECT r.id, m.all_types
            FROM ranked r
            JOIN merged_types m ON r.chat_id = m.chat_id AND r.tid = m.tid
            WHERE r.rn = 1
        )
        UPDATE telegram_notification_targets t
        SET types = k.all_types
        FROM keeper k
        WHERE t.id = k.id
    """)

    # 4. Also merge allow_incoming_tasks: keep TRUE if any duplicate had TRUE
    op.execute("""
        WITH ranked AS (
            SELECT id, chat_id, COALESCE(thread_id, 0) AS tid,
                   allow_incoming_tasks,
                   ROW_NUMBER() OVER (
                       PARTITION BY chat_id, COALESCE(thread_id, 0)
                       ORDER BY created_at
                   ) AS rn
            FROM telegram_notification_targets
        ),
        any_incoming AS (
            SELECT chat_id, tid, bool_or(allow_incoming_tasks) AS has_incoming
            FROM ranked
            GROUP BY chat_id, tid
        ),
        keeper AS (
            SELECT r.id, a.has_incoming
            FROM ranked r
            JOIN any_incoming a ON r.chat_id = a.chat_id AND r.tid = a.tid
            WHERE r.rn = 1
        )
        UPDATE telegram_notification_targets t
        SET allow_incoming_tasks = k.has_incoming
        FROM keeper k
        WHERE t.id = k.id
    """)

    # 5. Delete duplicate rows (keep only rn=1 per chat_id+thread_id)
    op.execute("""
        DELETE FROM telegram_notification_targets
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY chat_id, COALESCE(thread_id, 0)
                           ORDER BY created_at
                       ) AS rn
                FROM telegram_notification_targets
            ) sub
            WHERE rn > 1
        )
    """)

    # 6. Drop old 'type' column
    op.drop_column("telegram_notification_targets", "type")


def downgrade() -> None:
    # 1. Re-add 'type' column
    op.add_column(
        "telegram_notification_targets",
        sa.Column("type", sa.String(50), server_default="meeting"),
    )

    # 2. For each row with multiple types, duplicate the row for each type
    #    First, set type from first element of types array
    op.execute("""
        UPDATE telegram_notification_targets
        SET type = types[1]
    """)

    # 3. Insert additional rows for remaining types
    op.execute("""
        INSERT INTO telegram_notification_targets (id, chat_id, thread_id, label, type, allow_incoming_tasks, is_active, created_at)
        SELECT gen_random_uuid(), t.chat_id, t.thread_id, t.label, u.extra_type, t.allow_incoming_tasks, t.is_active, t.created_at
        FROM telegram_notification_targets t,
             LATERAL unnest(t.types[2:]) AS u(extra_type)
        WHERE array_length(t.types, 1) > 1
    """)

    # 4. Drop 'types' column
    op.drop_column("telegram_notification_targets", "types")
