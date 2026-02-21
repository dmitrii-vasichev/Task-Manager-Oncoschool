import unittest
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.services.meeting_scheduler_service import MeetingSchedulerService


class MeetingSchedulerZoomRulesTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_zoom_meeting_retries_and_succeeds(self) -> None:
        zoom_service = SimpleNamespace(
            create_meeting=AsyncMock(
                side_effect=[
                    RuntimeError("temporary zoom outage"),
                    {"id": "123", "join_url": "https://zoom.us/j/123"},
                ]
            )
        )
        scheduler = MeetingSchedulerService(
            bot=SimpleNamespace(send_message=AsyncMock()),
            session_maker=SimpleNamespace(),
            zoom_service=zoom_service,
        )
        schedule = SimpleNamespace(
            id=uuid.uuid4(),
            title="Планерка",
            duration_minutes=60,
            timezone="Europe/Moscow",
        )

        with patch("app.services.meeting_scheduler_service.asyncio.sleep", AsyncMock()):
            zoom_data = await scheduler._create_zoom_meeting_with_retry(
                schedule=schedule,
                meeting_date=datetime(2026, 2, 21, 12, 0, tzinfo=timezone.utc),
            )

        self.assertEqual(zoom_data["id"], "123")
        self.assertEqual(zoom_service.create_meeting.await_count, 2)

    async def test_create_zoom_meeting_retries_then_raises(self) -> None:
        zoom_service = SimpleNamespace(
            create_meeting=AsyncMock(side_effect=RuntimeError("zoom unavailable"))
        )
        scheduler = MeetingSchedulerService(
            bot=SimpleNamespace(send_message=AsyncMock()),
            session_maker=SimpleNamespace(),
            zoom_service=zoom_service,
        )
        schedule = SimpleNamespace(
            id=uuid.uuid4(),
            title="Планерка",
            duration_minutes=60,
            timezone="Europe/Moscow",
        )

        with patch("app.services.meeting_scheduler_service.asyncio.sleep", AsyncMock()):
            with self.assertRaisesRegex(RuntimeError, "after 3 attempts"):
                await scheduler._create_zoom_meeting_with_retry(
                    schedule=schedule,
                    meeting_date=datetime(2026, 2, 21, 12, 0, tzinfo=timezone.utc),
                )

        self.assertEqual(zoom_service.create_meeting.await_count, 3)

    async def test_send_reminders_raises_without_zoom_link(self) -> None:
        bot = SimpleNamespace(send_message=AsyncMock())
        scheduler = MeetingSchedulerService(
            bot=bot,
            session_maker=SimpleNamespace(),
            zoom_service=None,
        )
        schedule = SimpleNamespace(
            id=uuid.uuid4(),
            title="Планерка",
            reminder_text=None,
            participant_ids=[],
            reminder_include_zoom_link=True,
            telegram_targets=[{"chat_id": "12345", "thread_id": None}],
            time_utc=datetime(2026, 2, 21, 12, 0).time(),
        )
        meeting = SimpleNamespace(
            zoom_meeting_id=None,
            zoom_join_url=None,
            meeting_date=datetime(2026, 2, 21, 12, 0),
        )

        with self.assertRaisesRegex(RuntimeError, "Zoom link is missing"):
            await scheduler._send_reminders(
                session=SimpleNamespace(),
                schedule=schedule,
                meeting=meeting,
                zoom_data=None,
            )
        bot.send_message.assert_not_awaited()

    async def test_send_reminders_uses_zoom_id_fallback_url(self) -> None:
        bot = SimpleNamespace(send_message=AsyncMock())
        scheduler = MeetingSchedulerService(
            bot=bot,
            session_maker=SimpleNamespace(),
            zoom_service=None,
        )
        schedule = SimpleNamespace(
            id=uuid.uuid4(),
            title="Планерка",
            reminder_text=None,
            participant_ids=[],
            reminder_include_zoom_link=True,
            telegram_targets=[{"chat_id": "12345", "thread_id": None}],
            time_utc=datetime(2026, 2, 21, 12, 0).time(),
        )
        meeting = SimpleNamespace(
            zoom_meeting_id="987654321",
            zoom_join_url=None,
            meeting_date=datetime(2026, 2, 21, 12, 0),
        )

        await scheduler._send_reminders(
            session=SimpleNamespace(),
            schedule=schedule,
            meeting=meeting,
            zoom_data=None,
        )

        bot.send_message.assert_awaited_once()
        text = bot.send_message.await_args.kwargs["text"]
        self.assertIn("https://zoom.us/j/987654321", text)
