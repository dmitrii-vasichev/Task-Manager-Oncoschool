import unittest
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.api import meetings as meetings_api


class ManualMeetingDurationTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_meeting_passes_selected_duration_to_zoom(self) -> None:
        data = meetings_api.ManualMeetingCreate(
            title="Проверка длительности",
            meeting_date=datetime(2026, 2, 20, 12, 0, tzinfo=timezone.utc),
            timezone="Europe/Moscow",
            zoom_enabled=True,
            duration_minutes=90,
            participant_ids=[],
        )

        zoom_service = SimpleNamespace(
            create_meeting=AsyncMock(
                return_value={"id": "999", "join_url": "https://zoom.us/j/999"}
            )
        )
        request = SimpleNamespace(
            app=SimpleNamespace(state=SimpleNamespace(zoom_service=zoom_service))
        )
        member = SimpleNamespace(id=uuid.uuid4())
        session = SimpleNamespace(commit=AsyncMock())

        created_meeting = SimpleNamespace(id=uuid.uuid4())
        persisted_meeting = SimpleNamespace()

        with patch.object(
            meetings_api.meeting_service,
            "create_manual_meeting",
            AsyncMock(return_value=created_meeting),
        ) as create_manual_mock, patch.object(
            meetings_api.meeting_service,
            "get_meeting_by_id",
            AsyncMock(return_value=persisted_meeting),
        ) as get_by_id_mock, patch.object(
            meetings_api,
            "_meeting_response",
            lambda meeting: {"meeting": meeting},
        ):
            response = await meetings_api.create_meeting(
                data=data,
                request=request,
                member=member,
                session=session,
            )

        self.assertIs(response["meeting"], persisted_meeting)

        zoom_service.create_meeting.assert_awaited_once()
        zoom_call = zoom_service.create_meeting.await_args
        self.assertEqual(zoom_call.kwargs["duration"], 90)
        self.assertEqual(zoom_call.kwargs["timezone"], "Europe/Moscow")
        self.assertIsNone(zoom_call.kwargs["start_time"].tzinfo)

        create_manual_mock.assert_awaited_once()
        create_call = create_manual_mock.await_args
        self.assertIs(create_call.args[0], session)
        self.assertEqual(create_call.kwargs["duration_minutes"], 90)

        session.commit.assert_awaited_once()
        get_by_id_mock.assert_awaited_once_with(session, created_meeting.id)
