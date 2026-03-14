import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.api.meeting_schedules import _create_zoom_fields_for_occurrence


class MeetingScheduleZoomCreationTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_zoom_fields_returns_none_without_service(self) -> None:
        zoom_meeting_id, zoom_join_url = await _create_zoom_fields_for_occurrence(
            None,
            title="Планерка",
            occurrence_at=datetime(2026, 2, 21, 12, 0),
            duration_minutes=60,
            timezone="Europe/Moscow",
            context="test without service",
        )

        self.assertIsNone(zoom_meeting_id)
        self.assertIsNone(zoom_join_url)

    async def test_create_zoom_fields_creates_zoom_and_extracts_safe_join_url(self) -> None:
        zoom_service = SimpleNamespace(
            create_meeting=AsyncMock(
                return_value={
                    "id": "123456789",
                    "join_url": "https://zoom.us/j/123456789?zak=host-token&pwd=abc",
                }
            )
        )
        occurrence_at = datetime(2026, 2, 21, 12, 0)

        zoom_meeting_id, zoom_join_url = await _create_zoom_fields_for_occurrence(
            zoom_service,
            title="Планерка",
            occurrence_at=occurrence_at,
            duration_minutes=45,
            timezone="Europe/Moscow",
            context="test create",
        )

        self.assertEqual(zoom_meeting_id, "123456789")
        self.assertEqual(zoom_join_url, "https://zoom.us/j/123456789?pwd=abc")

        zoom_service.create_meeting.assert_awaited_once()
        call_kwargs = zoom_service.create_meeting.await_args.kwargs
        self.assertEqual(call_kwargs["topic"], "Планерка")
        self.assertEqual(call_kwargs["duration"], 45)
        self.assertEqual(call_kwargs["timezone"], "Europe/Moscow")
        self.assertEqual(
            call_kwargs["start_time"],
            occurrence_at.replace(tzinfo=timezone.utc),
        )

    async def test_create_zoom_fields_handles_zoom_errors(self) -> None:
        zoom_service = SimpleNamespace(
            create_meeting=AsyncMock(side_effect=RuntimeError("zoom unavailable"))
        )

        zoom_meeting_id, zoom_join_url = await _create_zoom_fields_for_occurrence(
            zoom_service,
            title="Планерка",
            occurrence_at=datetime(2026, 2, 21, 12, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            timezone="Europe/Moscow",
            context="test error handling",
        )

        self.assertIsNone(zoom_meeting_id)
        self.assertIsNone(zoom_join_url)
        zoom_service.create_meeting.assert_awaited_once()
