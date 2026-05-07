import uuid
from datetime import date, datetime, timedelta
from types import SimpleNamespace

from app.services.meeting_board_service import group_board_tasks


def task(**overrides):
    base = {
        "id": uuid.uuid4(),
        "short_id": 1,
        "status": "new",
        "priority": "normal",
        "deadline": None,
        "completed_at": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_group_board_tasks_keeps_overdue_inside_work_section() -> None:
    old_deadline = date.today() - timedelta(days=1)
    grouped = group_board_tasks(
        [
            task(short_id=10, status="in_progress", deadline=old_deadline),
            task(short_id=11, status="review", deadline=old_deadline),
        ],
        today=date.today(),
    )

    assert [t.short_id for t in grouped.in_progress] == [10]
    assert [t.short_id for t in grouped.review] == [11]
    assert grouped.urgent == []


def test_group_board_tasks_includes_done_this_week_only() -> None:
    now = datetime.utcnow()
    grouped = group_board_tasks(
        [
            task(short_id=20, status="done", completed_at=now - timedelta(days=2)),
            task(short_id=21, status="done", completed_at=now - timedelta(days=9)),
        ],
        today=date.today(),
        now=now,
    )

    assert [t.short_id for t in grouped.done_this_week] == [20]
