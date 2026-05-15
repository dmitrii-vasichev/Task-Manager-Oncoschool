import uuid
import unittest
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from types import SimpleNamespace

from app.services.content_factory.publication_service import (
    PublicationService,
    PublicationWorkflowTransitionError,
)
from app.db.schemas import (
    CFPublicationCreate,
    CFPublicationUpdate,
    CFPublicationVariantUpsert,
)


class TestPublicationService(unittest.IsolatedAsyncioTestCase):
    async def test_create_publication_with_initial_version(self):
        """Creating a publication should also create version 1 with approval_event=drafted."""
        session = AsyncMock()
        session.add = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        payload = CFPublicationCreate(
            bundle_id=uuid.uuid4(), platform_id=uuid.uuid4(),
            format_id=uuid.uuid4(), responsible_id=uuid.uuid4(),
            body_text="Initial draft text",
        )
        result = await PublicationService.create(session, payload, editor_id=payload.responsible_id)

        self.assertEqual(result.status, "draft")
        self.assertEqual(result.version_number, 1)
        # session.add called twice: once for publication, once for version
        self.assertEqual(session.add.call_count, 2)

    async def test_update_publication_creates_version_on_body_change(self):
        session = AsyncMock()
        publication = SimpleNamespace(
            id=uuid.uuid4(), bundle_id=uuid.uuid4(), body_text="old", version_number=1,
            status="draft", title="t",
        )
        PublicationService.get = AsyncMock(return_value=publication)

        editor_id = uuid.uuid4()
        result = await PublicationService.update(
            session, publication.id,
            CFPublicationUpdate(body_text="new text"),
            editor_id=editor_id,
            approval_event="reviewed",
        )
        self.assertEqual(result.body_text, "new text")
        self.assertEqual(result.version_number, 2)

    async def test_update_publication_creates_history_on_status_change(self):
        session = AsyncMock()
        publication = SimpleNamespace(
            id=uuid.uuid4(),
            bundle_id=uuid.uuid4(),
            body_text="ready text",
            version_number=1,
            status="needs_copy",
            title="t",
        )
        PublicationService.get = AsyncMock(return_value=publication)

        editor_id = uuid.uuid4()
        result = await PublicationService.update(
            session,
            publication.id,
            CFPublicationUpdate(status="factcheck"),
            editor_id=editor_id,
        )

        self.assertEqual(result.status, "factcheck")
        self.assertEqual(result.version_number, 2)
        version = session.add.call_args.args[0]
        self.assertEqual(version.version_number, 2)
        self.assertEqual(version.body_text, "ready text")
        self.assertEqual(version.edited_by_id, editor_id)
        self.assertEqual(version.approval_event, "reviewed")
        self.assertEqual(version.notes, "Статус: Нужен текст -> Фактчек")

    async def test_update_publication_body_and_status_creates_one_history_row(self):
        session = AsyncMock()
        publication = SimpleNamespace(
            id=uuid.uuid4(),
            bundle_id=uuid.uuid4(),
            body_text="old",
            version_number=1,
            status="doctor_review",
            title="t",
        )
        PublicationService.get = AsyncMock(return_value=publication)

        editor_id = uuid.uuid4()
        result = await PublicationService.update(
            session,
            publication.id,
            CFPublicationUpdate(body_text="new", status="approved"),
            editor_id=editor_id,
            approval_event="doctor_approved",
        )

        self.assertEqual(result.body_text, "new")
        self.assertEqual(result.status, "approved")
        self.assertEqual(result.version_number, 2)
        self.assertEqual(session.add.call_count, 1)
        version = session.add.call_args.args[0]
        self.assertEqual(version.body_text, "new")
        self.assertEqual(version.approval_event, "doctor_approved")
        self.assertEqual(version.notes, "Статус: Проверка врача -> Одобрено")

    async def test_update_publication_metadata_without_body_version(self):
        session = AsyncMock()
        platform_id = uuid.uuid4()
        format_id = uuid.uuid4()
        rubric_id = uuid.uuid4()
        nosology_id = uuid.uuid4()
        responsible_id = uuid.uuid4()
        publication = SimpleNamespace(
            id=uuid.uuid4(),
            bundle_id=uuid.uuid4(),
            platform_id=uuid.uuid4(),
            format_id=uuid.uuid4(),
            rubric_id=None,
            nosology_id=None,
            responsible_id=uuid.uuid4(),
            body_text="stable body",
            version_number=1,
            status="draft",
            title="t",
        )
        PublicationService.get = AsyncMock(return_value=publication)

        result = await PublicationService.update(
            session,
            publication.id,
            CFPublicationUpdate(
                platform_id=platform_id,
                format_id=format_id,
                rubric_id=rubric_id,
                nosology_id=nosology_id,
                responsible_id=responsible_id,
            ),
            editor_id=responsible_id,
            approval_event="reviewed",
        )

        self.assertEqual(result.platform_id, platform_id)
        self.assertEqual(result.format_id, format_id)
        self.assertEqual(result.rubric_id, rubric_id)
        self.assertEqual(result.nosology_id, nosology_id)
        self.assertEqual(result.responsible_id, responsible_id)
        self.assertEqual(result.version_number, 1)
        session.add.assert_not_called()

    async def test_update_publication_rejects_invalid_status_jump(self):
        session = AsyncMock()
        publication = SimpleNamespace(
            id=uuid.uuid4(),
            bundle_id=uuid.uuid4(),
            body_text="draft",
            version_number=1,
            status="draft",
            scheduled_at=None,
            title="t",
        )
        PublicationService.get = AsyncMock(return_value=publication)

        with self.assertRaisesRegex(
            PublicationWorkflowTransitionError,
            "Недопустимый переход статуса: Черновик -> Опубликовано",
        ):
            await PublicationService.update(
                session,
                publication.id,
                CFPublicationUpdate(status="published"),
                editor_id=uuid.uuid4(),
            )

        self.assertEqual(publication.status, "draft")
        session.add.assert_not_called()
        session.flush.assert_not_called()

    async def test_update_publication_rejects_scheduling_without_planned_date(self):
        session = AsyncMock()
        publication = SimpleNamespace(
            id=uuid.uuid4(),
            bundle_id=uuid.uuid4(),
            body_text="approved",
            version_number=1,
            status="approved",
            scheduled_at=None,
            title="t",
        )
        PublicationService.get = AsyncMock(return_value=publication)

        with self.assertRaisesRegex(
            PublicationWorkflowTransitionError,
            "Укажите плановую дату перед переводом в календарь",
        ):
            await PublicationService.update(
                session,
                publication.id,
                CFPublicationUpdate(status="scheduled"),
                editor_id=uuid.uuid4(),
            )

        self.assertEqual(publication.status, "approved")
        session.add.assert_not_called()
        session.flush.assert_not_called()

    async def test_update_publication_allows_scheduling_with_same_payload_date(self):
        session = AsyncMock()
        planned_at = datetime(2026, 5, 20, 10, 0, tzinfo=UTC)
        publication = SimpleNamespace(
            id=uuid.uuid4(),
            bundle_id=uuid.uuid4(),
            body_text="approved",
            version_number=1,
            status="approved",
            scheduled_at=None,
            title="t",
        )
        PublicationService.get = AsyncMock(return_value=publication)

        result = await PublicationService.update(
            session,
            publication.id,
            CFPublicationUpdate(status="scheduled", scheduled_at=planned_at),
            editor_id=uuid.uuid4(),
        )

        self.assertEqual(result.status, "scheduled")
        self.assertEqual(result.scheduled_at, planned_at)
        self.assertEqual(result.version_number, 2)
        version = session.add.call_args.args[0]
        self.assertEqual(version.approval_event, "scheduled")
        self.assertEqual(version.notes, "Статус: Одобрено -> Запланировано")

    async def test_upsert_variant_creates_saved_channel_variant(self):
        session = AsyncMock()
        publication = SimpleNamespace(
            id=uuid.uuid4(),
            version_number=3,
        )
        PublicationService.get = AsyncMock(return_value=publication)

        class EmptyResult:
            @staticmethod
            def scalar_one_or_none():
                return None

        session.execute = AsyncMock(return_value=EmptyResult())
        editor_id = uuid.uuid4()

        result = await PublicationService.upsert_variant(
            session,
            publication.id,
            "telegram",
            CFPublicationVariantUpsert(
                title="Telegram saved",
                body_text="Saved body",
                notes="Use registration link",
            ),
            editor_id=editor_id,
        )

        self.assertEqual(result.publication_id, publication.id)
        self.assertEqual(result.channel, "telegram")
        self.assertEqual(result.title, "Telegram saved")
        self.assertEqual(result.body_text, "Saved body")
        self.assertEqual(result.notes, "Use registration link")
        self.assertEqual(result.source_version_number, 3)
        self.assertEqual(result.updated_by_id, editor_id)
        session.add.assert_called_once()
        session.flush.assert_awaited()

    async def test_upsert_variant_updates_existing_channel_variant(self):
        session = AsyncMock()
        publication = SimpleNamespace(
            id=uuid.uuid4(),
            version_number=4,
        )
        existing = SimpleNamespace(
            id=uuid.uuid4(),
            publication_id=publication.id,
            channel="vk",
            title="Old",
            body_text="Old body",
            notes=None,
            source_version_number=2,
            updated_by_id=uuid.uuid4(),
            updated_at=None,
        )
        PublicationService.get = AsyncMock(return_value=publication)

        class ExistingResult:
            @staticmethod
            def scalar_one_or_none():
                return existing

        session.execute = AsyncMock(return_value=ExistingResult())
        editor_id = uuid.uuid4()

        result = await PublicationService.upsert_variant(
            session,
            publication.id,
            "vk",
            CFPublicationVariantUpsert(
                title="New",
                body_text="New body",
                notes="Updated note",
            ),
            editor_id=editor_id,
        )

        self.assertIs(result, existing)
        self.assertEqual(existing.title, "New")
        self.assertEqual(existing.body_text, "New body")
        self.assertEqual(existing.notes, "Updated note")
        self.assertEqual(existing.source_version_number, 4)
        self.assertEqual(existing.updated_by_id, editor_id)
        self.assertIsNotNone(existing.updated_at)
        session.add.assert_not_called()
        session.flush.assert_awaited()

    async def test_upsert_variant_returns_none_for_missing_publication(self):
        session = AsyncMock()
        PublicationService.get = AsyncMock(return_value=None)

        result = await PublicationService.upsert_variant(
            session,
            uuid.uuid4(),
            "telegram",
            CFPublicationVariantUpsert(body_text="Saved body"),
            editor_id=uuid.uuid4(),
        )

        self.assertIsNone(result)
        session.add.assert_not_called()
        session.flush.assert_not_called()


if __name__ == "__main__":
    unittest.main()
