import unittest
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from app.db.schemas import CFGuestStoryCreate, CFGuestStoryUpdate
from app.services.content_factory.guest_story_service import GuestStoryService


class _FakeScalars:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return _FakeScalars(self._rows)


class TestGuestStoryService(unittest.IsolatedAsyncioTestCase):
    async def test_create_guest_story(self):
        session = AsyncMock()
        session.add = Mock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        owner_id = uuid.uuid4()

        payload = CFGuestStoryCreate(
            display_name="Patient story candidate",
            role="patient",
            owner_id=owner_id,
            story_brief="Useful patient experience for a live event.",
            allowed_channels=["telegram", "vk"],
            sensitive_topics=["doctor_name"],
        )

        result = await GuestStoryService.create(session, payload)

        self.assertEqual(result.display_name, payload.display_name)
        self.assertEqual(result.role, "patient")
        self.assertEqual(result.status, "sourced")
        self.assertEqual(result.owner_id, owner_id)
        self.assertEqual(result.allowed_channels, ["telegram", "vk"])
        session.add.assert_called_once()
        session.flush.assert_awaited()
        session.refresh.assert_awaited_with(result)

    async def test_list_guest_stories_returns_rows(self):
        story = SimpleNamespace(
            id=uuid.uuid4(),
            display_name="Candidate",
            status="consent_sent",
            consent_status="sent",
            owner_id=uuid.uuid4(),
            stage_due_at=datetime.now(UTC),
        )
        session = AsyncMock()
        session.execute = AsyncMock(return_value=_FakeResult([story]))

        result = await GuestStoryService.list(
            session,
            status="consent_sent",
            owner_id=story.owner_id,
            consent_status="sent",
            bundle_id=None,
            publication_id=None,
            limit=25,
            offset=0,
        )

        self.assertEqual(result, [story])
        session.execute.assert_awaited_once()

    async def test_update_guest_story_partial(self):
        story = SimpleNamespace(
            id=uuid.uuid4(),
            display_name="Old",
            status="sourced",
            consent_status="not_started",
            allowed_channels=[],
        )
        payload = CFGuestStoryUpdate(
            status="consent_signed",
            consent_status="signed",
            allowed_channels=["telegram"],
        )
        session = AsyncMock()
        session.flush = AsyncMock()

        with patch.object(GuestStoryService, "get", AsyncMock(return_value=story)):
            result = await GuestStoryService.update(session, story.id, payload)

        self.assertEqual(result.status, "consent_signed")
        self.assertEqual(result.consent_status, "signed")
        self.assertEqual(result.allowed_channels, ["telegram"])
        self.assertEqual(result.display_name, "Old")
        session.flush.assert_awaited()


if __name__ == "__main__":
    unittest.main()
