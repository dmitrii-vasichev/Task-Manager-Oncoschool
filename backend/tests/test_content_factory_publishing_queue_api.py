import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api.content_factory import publishing_queue as queue_api
from app.db.schemas import CFPublishingQueueManualFallbackRequest
from app.services.content_factory.publishing_queue_service import (
    PublishingQueueValidationError,
)


def cf_member(role="member", has_cf=True):
    return SimpleNamespace(
        id=uuid.uuid4(),
        role=role,
        is_active=True,
        has_content_factory_access=has_cf,
    )


def make_queue_item(**overrides):
    base = {
        "id": uuid.uuid4(),
        "publication_id": uuid.uuid4(),
        "platform_id": uuid.uuid4(),
        "status": "queued",
        "scheduled_for": datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
        "requested_by_id": uuid.uuid4(),
        "attempts": 0,
        "max_attempts": 3,
        "last_attempt_at": None,
        "next_retry_at": None,
        "completed_at": None,
        "error_message": None,
        "manual_fallback_reason": None,
        "payload": {},
        "provider_response": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def make_event(**overrides):
    base = {
        "id": uuid.uuid4(),
        "queue_item_id": uuid.uuid4(),
        "publication_id": uuid.uuid4(),
        "actor_id": uuid.uuid4(),
        "event_type": "queued",
        "message": "Queued",
        "payload": {},
        "created_at": datetime.now(UTC),
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_list_publishing_queue_passes_filters(monkeypatch):
    session = AsyncMock()
    publication_id = uuid.uuid4()
    items = [make_queue_item(publication_id=publication_id, status="failed")]
    monkeypatch.setattr(
        queue_api.publishing_queue_service,
        "list_items",
        AsyncMock(return_value=items),
    )

    result = await queue_api.list_publishing_queue(
        member=cf_member(),
        session=session,
        status="failed",
        publication_id=publication_id,
        limit=25,
        offset=5,
    )

    assert result == items
    queue_api.publishing_queue_service.list_items.assert_awaited_once_with(
        session,
        status="failed",
        publication_id=publication_id,
        limit=25,
        offset=5,
    )


@pytest.mark.asyncio
async def test_enqueue_publication_for_publishing_persists(monkeypatch):
    session = AsyncMock()
    member = cf_member()
    publication_id = uuid.uuid4()
    item = make_queue_item(publication_id=publication_id, requested_by_id=member.id)
    monkeypatch.setattr(
        queue_api.publishing_queue_service,
        "enqueue_publication",
        AsyncMock(return_value=item),
    )

    result = await queue_api.enqueue_publication_for_publishing(
        publication_id=publication_id,
        member=member,
        session=session,
    )

    assert result is item
    queue_api.publishing_queue_service.enqueue_publication.assert_awaited_once_with(
        session,
        publication_id,
        actor_id=member.id,
    )
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_enqueue_publication_for_publishing_404(monkeypatch):
    session = AsyncMock()
    monkeypatch.setattr(
        queue_api.publishing_queue_service,
        "enqueue_publication",
        AsyncMock(return_value=None),
    )

    with pytest.raises(HTTPException) as exc:
        await queue_api.enqueue_publication_for_publishing(
            publication_id=uuid.uuid4(),
            member=cf_member(),
            session=session,
        )

    assert exc.value.status_code == 404
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_enqueue_publication_for_publishing_validation_400(monkeypatch):
    session = AsyncMock()
    monkeypatch.setattr(
        queue_api.publishing_queue_service,
        "enqueue_publication",
        AsyncMock(
            side_effect=PublishingQueueValidationError(
                "Сначала доведите публикацию до статуса Одобрено или Запланировано"
            )
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await queue_api.enqueue_publication_for_publishing(
            publication_id=uuid.uuid4(),
            member=cf_member(),
            session=session,
        )

    assert exc.value.status_code == 400
    assert "Сначала доведите публикацию" in exc.value.detail
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_publishing_queue_for_publication(monkeypatch):
    publication_id = uuid.uuid4()
    items = [make_queue_item(publication_id=publication_id)]
    monkeypatch.setattr(
        queue_api.publishing_queue_service,
        "list_for_publication",
        AsyncMock(return_value=items),
    )

    result = await queue_api.list_publishing_queue_for_publication(
        publication_id=publication_id,
        member=cf_member(),
        session=AsyncMock(),
    )

    assert result == items


@pytest.mark.asyncio
async def test_retry_publishing_queue_item(monkeypatch):
    session = AsyncMock()
    member = cf_member()
    item = make_queue_item(status="queued")
    monkeypatch.setattr(
        queue_api.publishing_queue_service,
        "retry_item",
        AsyncMock(return_value=item),
    )

    result = await queue_api.retry_publishing_queue_item(
        queue_item_id=item.id,
        member=member,
        session=session,
    )

    assert result is item
    queue_api.publishing_queue_service.retry_item.assert_awaited_once_with(
        session,
        item.id,
        actor_id=member.id,
    )
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_retry_publishing_queue_item_validation_400(monkeypatch):
    session = AsyncMock()
    monkeypatch.setattr(
        queue_api.publishing_queue_service,
        "retry_item",
        AsyncMock(
            side_effect=PublishingQueueValidationError(
                "Повторить можно только неуспешную отправку или ручной fallback"
            )
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await queue_api.retry_publishing_queue_item(
            queue_item_id=uuid.uuid4(),
            member=cf_member(),
            session=session,
        )

    assert exc.value.status_code == 400
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_mark_publishing_queue_manual_fallback(monkeypatch):
    session = AsyncMock()
    member = cf_member()
    item = make_queue_item(status="manual_fallback")
    monkeypatch.setattr(
        queue_api.publishing_queue_service,
        "mark_manual_fallback",
        AsyncMock(return_value=item),
    )

    result = await queue_api.mark_publishing_queue_manual_fallback(
        queue_item_id=item.id,
        data=CFPublishingQueueManualFallbackRequest(reason="Use manual package"),
        member=member,
        session=session,
    )

    assert result is item
    queue_api.publishing_queue_service.mark_manual_fallback.assert_awaited_once_with(
        session,
        item.id,
        actor_id=member.id,
        reason="Use manual package",
    )
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_list_publishing_queue_events(monkeypatch):
    item_id = uuid.uuid4()
    events = [make_event(queue_item_id=item_id)]
    monkeypatch.setattr(
        queue_api.publishing_queue_service,
        "list_events",
        AsyncMock(return_value=events),
    )

    result = await queue_api.list_publishing_queue_events(
        queue_item_id=item_id,
        member=cf_member(),
        session=AsyncMock(),
    )

    assert result == events
