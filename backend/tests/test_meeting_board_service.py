import uuid
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.services.meeting_board_service import MeetingBoardService, group_board_tasks


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


class FakeScalarResult:
    def __init__(self, tasks):
        self.tasks = tasks

    def unique(self):
        return self

    def all(self):
        return self.tasks


class FakeExecuteResult:
    def __init__(self, tasks):
        self.tasks = tasks

    def scalars(self):
        return FakeScalarResult(self.tasks)


@pytest.mark.asyncio
async def test_load_visible_tasks_rechecks_pinned_task_access() -> None:
    allowed_task = task(short_id=30)
    blocked_task = task(short_id=31)
    session = SimpleNamespace(
        execute=AsyncMock(return_value=FakeExecuteResult([allowed_task, blocked_task]))
    )
    service = MeetingBoardService()
    meeting = SimpleNamespace(participants=[])
    settings = SimpleNamespace(
        added_member_ids=[],
        added_department_ids=[],
        pinned_task_ids=[allowed_task.id, blocked_task.id],
    )
    viewer = SimpleNamespace(id=uuid.uuid4())

    can_access = AsyncMock(side_effect=[True, False])
    with patch(
        "app.services.meeting_board_service.resolve_visible_department_ids",
        AsyncMock(return_value=None),
    ) as resolve_visible_department_ids, patch(
        "app.services.meeting_board_service.can_access_task",
        can_access,
    ):
        visible_tasks = await service._load_visible_tasks(
            session, meeting, settings, viewer
        )

    assert visible_tasks == [allowed_task]
    resolve_visible_department_ids.assert_awaited_once_with(session, viewer)
    assert can_access.await_count == 2
    can_access.assert_any_await(session, viewer, allowed_task)
    can_access.assert_any_await(session, viewer, blocked_task)
