import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.db.models import CFPublishingQueueEvent, CFPublishingQueueItem
from app.services.content_factory.publishing_queue_service import (
    PublishingQueueService,
    PublishingQueueValidationError,
)


def make_publication(**overrides):
    base = {
        "id": uuid.uuid4(),
        "platform_id": uuid.uuid4(),
        "title": "Telegram announcement",
        "body_text": "Post body",
        "media_refs": ["image.png"],
        "scheduled_at": datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
        "status": "scheduled",
        "utm": {"utm_campaign": "may_live"},
        "version_number": 3,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def make_queue_item(**overrides):
    base = {
        "id": uuid.uuid4(),
        "publication_id": uuid.uuid4(),
        "platform_id": uuid.uuid4(),
        "status": "failed",
        "scheduled_for": datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
        "requested_by_id": uuid.uuid4(),
        "attempts": 1,
        "max_attempts": 3,
        "last_attempt_at": None,
        "next_retry_at": None,
        "completed_at": None,
        "error_message": "Timeout",
        "manual_fallback_reason": None,
        "payload": {},
        "provider_response": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def make_session():
    return SimpleNamespace(
        add=Mock(),
        flush=AsyncMock(),
        execute=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_enqueue_publication_creates_queue_item_and_audit_event(monkeypatch):
    session = make_session()
    publication = make_publication()
    actor_id = uuid.uuid4()
    monkeypatch.setattr(
        PublishingQueueService,
        "get_publication",
        AsyncMock(return_value=publication),
    )
    monkeypatch.setattr(
        PublishingQueueService,
        "get_active_item_for_publication",
        AsyncMock(return_value=None),
    )

    item = await PublishingQueueService.enqueue_publication(
        session,
        publication.id,
        actor_id=actor_id,
    )

    assert isinstance(item, CFPublishingQueueItem)
    assert item.publication_id == publication.id
    assert item.platform_id == publication.platform_id
    assert item.status == "queued"
    assert item.scheduled_for == publication.scheduled_at
    assert item.requested_by_id == actor_id
    assert item.payload["title"] == "Telegram announcement"
    assert item.payload["status_at_enqueue"] == "scheduled"
    assert item.payload["version_number"] == 3
    assert session.add.call_count == 2
    event = session.add.call_args_list[1].args[0]
    assert isinstance(event, CFPublishingQueueEvent)
    assert event.queue_item_id == item.id
    assert event.event_type == "queued"
    assert event.actor_id == actor_id
    session.flush.assert_awaited()


@pytest.mark.asyncio
async def test_enqueue_publication_returns_existing_active_item(monkeypatch):
    session = make_session()
    publication = make_publication()
    existing = make_queue_item(
        publication_id=publication.id,
        platform_id=publication.platform_id,
        status="queued",
    )
    monkeypatch.setattr(
        PublishingQueueService,
        "get_publication",
        AsyncMock(return_value=publication),
    )
    monkeypatch.setattr(
        PublishingQueueService,
        "get_active_item_for_publication",
        AsyncMock(return_value=existing),
    )

    item = await PublishingQueueService.enqueue_publication(
        session,
        publication.id,
        actor_id=uuid.uuid4(),
    )

    assert item is existing
    session.add.assert_not_called()
    session.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_enqueue_publication_rejects_early_workflow_status(monkeypatch):
    session = make_session()
    publication = make_publication(status="draft")
    monkeypatch.setattr(
        PublishingQueueService,
        "get_publication",
        AsyncMock(return_value=publication),
    )
    monkeypatch.setattr(
        PublishingQueueService,
        "get_active_item_for_publication",
        AsyncMock(return_value=None),
    )

    with pytest.raises(PublishingQueueValidationError) as exc:
        await PublishingQueueService.enqueue_publication(
            session,
            publication.id,
            actor_id=uuid.uuid4(),
        )

    assert "Сначала доведите публикацию" in str(exc.value)
    session.add.assert_not_called()
    session.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_retry_item_moves_failed_job_back_to_queue_and_records_event(monkeypatch):
    session = make_session()
    actor_id = uuid.uuid4()
    item = make_queue_item(
        status="failed",
        error_message="Gateway timeout",
        manual_fallback_reason=None,
        completed_at=datetime(2026, 5, 20, 10, 5, tzinfo=UTC),
    )
    monkeypatch.setattr(
        PublishingQueueService,
        "get_item",
        AsyncMock(return_value=item),
    )

    result = await PublishingQueueService.retry_item(
        session,
        item.id,
        actor_id=actor_id,
    )

    assert result is item
    assert item.status == "queued"
    assert item.error_message is None
    assert item.manual_fallback_reason is None
    assert item.completed_at is None
    event = session.add.call_args.args[0]
    assert isinstance(event, CFPublishingQueueEvent)
    assert event.event_type == "retry_requested"
    assert event.actor_id == actor_id
    session.flush.assert_awaited()


@pytest.mark.asyncio
async def test_retry_item_rejects_active_job(monkeypatch):
    session = make_session()
    item = make_queue_item(status="queued")
    monkeypatch.setattr(
        PublishingQueueService,
        "get_item",
        AsyncMock(return_value=item),
    )

    with pytest.raises(PublishingQueueValidationError) as exc:
        await PublishingQueueService.retry_item(
            session,
            item.id,
            actor_id=uuid.uuid4(),
        )

    assert "Повторить можно только" in str(exc.value)
    session.add.assert_not_called()
    session.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_manual_fallback_completes_item_and_records_reason(monkeypatch):
    session = make_session()
    actor_id = uuid.uuid4()
    item = make_queue_item(status="failed", manual_fallback_reason=None)
    monkeypatch.setattr(
        PublishingQueueService,
        "get_item",
        AsyncMock(return_value=item),
    )

    result = await PublishingQueueService.mark_manual_fallback(
        session,
        item.id,
        actor_id=actor_id,
        reason="Token needs manual renewal",
    )

    assert result is item
    assert item.status == "manual_fallback"
    assert item.manual_fallback_reason == "Token needs manual renewal"
    assert item.completed_at is not None
    event = session.add.call_args.args[0]
    assert event.event_type == "manual_fallback"
    assert event.message == "Token needs manual renewal"
    session.flush.assert_awaited()


@pytest.mark.asyncio
async def test_record_attempt_failure_sets_retry_metadata_before_max_attempts():
    session = make_session()
    item = make_queue_item(status="processing", attempts=0, max_attempts=3)

    result = await PublishingQueueService.record_attempt_failure(
        session,
        item,
        error_message="Temporary provider error",
        retry_after=timedelta(minutes=15),
    )

    assert result is item
    assert item.status == "queued"
    assert item.attempts == 1
    assert item.error_message == "Temporary provider error"
    assert item.next_retry_at is not None
    event = session.add.call_args.args[0]
    assert event.event_type == "failed"
    assert event.payload["will_retry"] is True
    session.flush.assert_awaited()


@pytest.mark.asyncio
async def test_record_attempt_failure_marks_failed_at_max_attempts():
    session = make_session()
    item = make_queue_item(status="processing", attempts=2, max_attempts=3)

    result = await PublishingQueueService.record_attempt_failure(
        session,
        item,
        error_message="Permanent provider error",
    )

    assert result is item
    assert item.status == "failed"
    assert item.attempts == 3
    assert item.completed_at is not None
    assert item.next_retry_at is None
    event = session.add.call_args.args[0]
    assert event.event_type == "failed"
    assert event.payload["will_retry"] is False
    session.flush.assert_awaited()
