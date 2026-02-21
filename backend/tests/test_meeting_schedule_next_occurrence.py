import unittest
from datetime import datetime, time, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

from app.api.meeting_schedules import (
    _calc_next_occurrence_date,
    _sync_next_scheduled_meeting,
)


class MeetingScheduleNextOccurrenceTests(unittest.TestCase):
    def test_weekly_next_occurrence_respects_skip_flag(self) -> None:
        now_utc = datetime.now(ZoneInfo("UTC"))
        next_day = now_utc.date() + timedelta(days=1)

        schedule = SimpleNamespace(
            recurrence="weekly",
            timezone="UTC",
            day_of_week=next_day.isoweekday(),
            time_utc=time(12, 0),
            next_occurrence_time_override=None,
            next_occurrence_skip=False,
            last_triggered_date=None,
        )

        self.assertEqual(_calc_next_occurrence_date(schedule), next_day)

        schedule.next_occurrence_skip = True
        self.assertEqual(
            _calc_next_occurrence_date(schedule),
            next_day + timedelta(days=7),
        )


class MeetingScheduleSyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_sync_next_scheduled_meeting_reschedules_zoom_on_skip(self) -> None:
        now_utc = datetime.now(ZoneInfo("UTC"))
        next_day = now_utc.date() + timedelta(days=1)
        old_dt = datetime.combine(next_day, time(12, 0))
        expected_dt = old_dt + timedelta(days=7)

        schedule = SimpleNamespace(
            id="schedule-id",
            title="Планерка",
            recurrence="weekly",
            timezone="UTC",
            day_of_week=next_day.isoweekday(),
            time_utc=time(12, 0),
            next_occurrence_time_override=None,
            next_occurrence_skip=True,
            last_triggered_date=None,
            duration_minutes=60,
            zoom_enabled=True,
            participant_ids=[],
            created_by_id=None,
        )

        meeting = SimpleNamespace(
            meeting_date=old_dt,
            title="Планерка",
            duration_minutes=60,
            status="scheduled",
            sent_reminder_offsets_minutes=[60, 0],
            zoom_meeting_id="123",
            zoom_join_url="https://zoom.us/j/123",
        )

        zoom_service = SimpleNamespace(update_meeting=AsyncMock())

        with patch(
            "app.api.meeting_schedules._find_next_scheduled_meeting_with_date",
            AsyncMock(return_value=meeting),
        ):
            await _sync_next_scheduled_meeting(
                session=SimpleNamespace(),
                schedule=schedule,
                zoom_service=zoom_service,
            )

        self.assertEqual(meeting.meeting_date, expected_dt)
        self.assertEqual(meeting.sent_reminder_offsets_minutes, [])
        zoom_service.update_meeting.assert_awaited_once()
        zoom_call = zoom_service.update_meeting.await_args
        self.assertEqual(zoom_call.args[0], "123")
        self.assertEqual(
            zoom_call.kwargs["start_time"],
            expected_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        )
