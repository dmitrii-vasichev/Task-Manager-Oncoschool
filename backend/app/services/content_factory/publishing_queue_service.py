from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CFPublication, CFPublishingQueueEvent, CFPublishingQueueItem


class PublishingQueueValidationError(ValueError):
    """Raised when a publishing queue operation is not allowed."""


ACTIVE_QUEUE_STATUSES = ("queued", "processing")
ENQUEUEABLE_PUBLICATION_STATUSES = {"approved", "scheduled"}
RETRYABLE_QUEUE_STATUSES = {"failed", "manual_fallback"}
MANUAL_FALLBACK_BLOCKED_STATUSES = {"succeeded", "cancelled"}


def _datetime_to_json(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _publication_payload(publication: CFPublication) -> dict[str, Any]:
    return {
        "publication_id": str(publication.id),
        "platform_id": str(publication.platform_id),
        "title": publication.title,
        "body_text": publication.body_text,
        "media_refs": publication.media_refs,
        "scheduled_at": _datetime_to_json(publication.scheduled_at),
        "status_at_enqueue": publication.status,
        "utm": publication.utm,
        "version_number": publication.version_number,
    }


def _queue_event(
    item: CFPublishingQueueItem,
    *,
    event_type: str,
    actor_id: uuid.UUID | None,
    message: str | None = None,
    payload: dict[str, Any] | None = None,
) -> CFPublishingQueueEvent:
    return CFPublishingQueueEvent(
        id=uuid.uuid4(),
        queue_item_id=item.id,
        publication_id=item.publication_id,
        actor_id=actor_id,
        event_type=event_type,
        message=message,
        payload=payload or {},
    )


class PublishingQueueService:
    @staticmethod
    async def get_publication(
        session: AsyncSession,
        publication_id: uuid.UUID,
    ) -> CFPublication | None:
        return await session.get(CFPublication, publication_id)

    @staticmethod
    async def get_item(
        session: AsyncSession,
        queue_item_id: uuid.UUID,
    ) -> CFPublishingQueueItem | None:
        return await session.get(CFPublishingQueueItem, queue_item_id)

    @staticmethod
    async def get_active_item_for_publication(
        session: AsyncSession,
        publication_id: uuid.UUID,
    ) -> CFPublishingQueueItem | None:
        result = await session.execute(
            select(CFPublishingQueueItem)
            .where(
                CFPublishingQueueItem.publication_id == publication_id,
                CFPublishingQueueItem.status.in_(ACTIVE_QUEUE_STATUSES),
            )
            .order_by(CFPublishingQueueItem.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def enqueue_publication(
        session: AsyncSession,
        publication_id: uuid.UUID,
        *,
        actor_id: uuid.UUID,
    ) -> CFPublishingQueueItem | None:
        publication = await PublishingQueueService.get_publication(
            session,
            publication_id,
        )
        if publication is None:
            return None

        if publication.status not in ENQUEUEABLE_PUBLICATION_STATUSES:
            raise PublishingQueueValidationError(
                "Сначала доведите публикацию до статуса Одобрено или Запланировано"
            )

        active_item = await PublishingQueueService.get_active_item_for_publication(
            session,
            publication_id,
        )
        if active_item is not None:
            return active_item

        item = CFPublishingQueueItem(
            id=uuid.uuid4(),
            publication_id=publication.id,
            platform_id=publication.platform_id,
            status="queued",
            scheduled_for=publication.scheduled_at,
            requested_by_id=actor_id,
            attempts=0,
            max_attempts=3,
            payload=_publication_payload(publication),
        )
        session.add(item)
        await session.flush()

        session.add(
            _queue_event(
                item,
                event_type="queued",
                actor_id=actor_id,
                message="Publication was queued for platform-neutral publishing.",
                payload={"source": "operator"},
            )
        )
        await session.flush()
        return item

    @staticmethod
    async def list_items(
        session: AsyncSession,
        *,
        status: str | None = None,
        publication_id: uuid.UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CFPublishingQueueItem]:
        stmt = select(CFPublishingQueueItem)
        if status:
            stmt = stmt.where(CFPublishingQueueItem.status == status)
        if publication_id:
            stmt = stmt.where(CFPublishingQueueItem.publication_id == publication_id)
        stmt = stmt.order_by(
            CFPublishingQueueItem.created_at.desc(),
        ).limit(limit).offset(offset)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def list_for_publication(
        session: AsyncSession,
        publication_id: uuid.UUID,
    ) -> list[CFPublishingQueueItem]:
        return await PublishingQueueService.list_items(
            session,
            publication_id=publication_id,
            limit=50,
            offset=0,
        )

    @staticmethod
    async def list_events(
        session: AsyncSession,
        queue_item_id: uuid.UUID,
    ) -> list[CFPublishingQueueEvent]:
        result = await session.execute(
            select(CFPublishingQueueEvent)
            .where(CFPublishingQueueEvent.queue_item_id == queue_item_id)
            .order_by(CFPublishingQueueEvent.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_due_items(
        session: AsyncSession,
        *,
        now: datetime,
        limit: int = 50,
    ) -> list[CFPublishingQueueItem]:
        result = await session.execute(
            select(CFPublishingQueueItem)
            .where(
                CFPublishingQueueItem.status == "queued",
                or_(
                    CFPublishingQueueItem.scheduled_for.is_(None),
                    CFPublishingQueueItem.scheduled_for <= now,
                ),
                or_(
                    CFPublishingQueueItem.next_retry_at.is_(None),
                    CFPublishingQueueItem.next_retry_at <= now,
                ),
            )
            .order_by(
                CFPublishingQueueItem.scheduled_for.asc().nullsfirst(),
                CFPublishingQueueItem.created_at.asc(),
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def mark_processing(
        session: AsyncSession,
        item: CFPublishingQueueItem,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> CFPublishingQueueItem:
        now = datetime.now(timezone.utc)
        item.status = "processing"
        item.last_attempt_at = now
        item.error_message = None
        item.updated_at = now
        session.add(
            _queue_event(
                item,
                event_type="started",
                actor_id=actor_id,
                message="Publishing attempt started.",
                payload={"attempt": (item.attempts or 0) + 1},
            )
        )
        await session.flush()
        return item

    @staticmethod
    async def record_attempt_success(
        session: AsyncSession,
        item: CFPublishingQueueItem,
        *,
        provider_response: dict[str, Any],
        actor_id: uuid.UUID | None = None,
    ) -> CFPublishingQueueItem:
        now = datetime.now(timezone.utc)
        item.status = "succeeded"
        item.attempts = (item.attempts or 0) + 1
        item.last_attempt_at = now
        item.next_retry_at = None
        item.completed_at = now
        item.error_message = None
        item.provider_response = provider_response
        item.updated_at = now
        session.add(
            _queue_event(
                item,
                event_type="succeeded",
                actor_id=actor_id,
                message="Publishing attempt succeeded.",
                payload=provider_response,
            )
        )
        await session.flush()
        return item

    @staticmethod
    async def retry_item(
        session: AsyncSession,
        queue_item_id: uuid.UUID,
        *,
        actor_id: uuid.UUID,
    ) -> CFPublishingQueueItem | None:
        item = await PublishingQueueService.get_item(session, queue_item_id)
        if item is None:
            return None
        if item.status not in RETRYABLE_QUEUE_STATUSES:
            raise PublishingQueueValidationError(
                "Повторить можно только неуспешную отправку или ручной fallback"
            )

        now = datetime.now(timezone.utc)
        item.status = "queued"
        item.error_message = None
        item.manual_fallback_reason = None
        item.next_retry_at = None
        item.completed_at = None
        item.updated_at = now
        session.add(
            _queue_event(
                item,
                event_type="retry_requested",
                actor_id=actor_id,
                message="Retry requested by operator.",
            )
        )
        await session.flush()
        return item

    @staticmethod
    async def mark_manual_fallback(
        session: AsyncSession,
        queue_item_id: uuid.UUID,
        *,
        actor_id: uuid.UUID,
        reason: str,
    ) -> CFPublishingQueueItem | None:
        item = await PublishingQueueService.get_item(session, queue_item_id)
        if item is None:
            return None
        if item.status in MANUAL_FALLBACK_BLOCKED_STATUSES:
            raise PublishingQueueValidationError(
                "Для завершённой или отменённой отправки ручной обход не нужен"
            )

        now = datetime.now(timezone.utc)
        fallback_reason = reason.strip()
        item.status = "manual_fallback"
        item.manual_fallback_reason = fallback_reason
        item.completed_at = now
        item.updated_at = now
        session.add(
            _queue_event(
                item,
                event_type="manual_fallback",
                actor_id=actor_id,
                message=fallback_reason,
            )
        )
        await session.flush()
        return item

    @staticmethod
    async def record_attempt_failure(
        session: AsyncSession,
        item: CFPublishingQueueItem,
        *,
        error_message: str,
        retry_after: timedelta | None = None,
        provider_response: dict[str, Any] | None = None,
    ) -> CFPublishingQueueItem:
        now = datetime.now(timezone.utc)
        item.attempts = (item.attempts or 0) + 1
        item.last_attempt_at = now
        item.error_message = error_message
        item.provider_response = provider_response
        item.updated_at = now
        will_retry = item.attempts < (item.max_attempts or 3) and retry_after is not None
        if will_retry:
            item.status = "queued"
            item.next_retry_at = now + retry_after
            item.completed_at = None
        else:
            item.status = "failed"
            item.next_retry_at = None
            item.completed_at = now

        session.add(
            _queue_event(
                item,
                event_type="failed",
                actor_id=None,
                message=error_message,
                payload={
                    "attempts": item.attempts,
                    "max_attempts": item.max_attempts,
                    "will_retry": will_retry,
                    "provider_response": provider_response,
                },
            )
        )
        await session.flush()
        return item
