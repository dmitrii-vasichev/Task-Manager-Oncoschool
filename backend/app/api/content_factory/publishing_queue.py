"""Publishing queue endpoints for Content Factory publications."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.content_factory.deps import require_cf_access
from app.db.database import get_session
from app.db.models import TeamMember
from app.db.schemas import (
    CFPublishingQueueEventResponse,
    CFPublishingQueueItemResponse,
    CFPublishingQueueManualFallbackRequest,
)
from app.services.content_factory.publishing_queue_service import (
    PublishingQueueService,
    PublishingQueueValidationError,
)

router = APIRouter(tags=["content-factory"])
publishing_queue_service = PublishingQueueService


@router.get(
    "/publishing-queue",
    response_model=list[CFPublishingQueueItemResponse],
)
async def list_publishing_queue(
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
    status: str | None = Query(default=None),
    publication_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    return await publishing_queue_service.list_items(
        session,
        status=status,
        publication_id=publication_id,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/publications/{publication_id}/publishing-queue",
    response_model=CFPublishingQueueItemResponse,
    status_code=201,
)
async def enqueue_publication_for_publishing(
    publication_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    try:
        item = await publishing_queue_service.enqueue_publication(
            session,
            publication_id,
            actor_id=member.id,
        )
    except PublishingQueueValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Публикация не найдена")
    await session.commit()
    return item


@router.get(
    "/publications/{publication_id}/publishing-queue",
    response_model=list[CFPublishingQueueItemResponse],
)
async def list_publishing_queue_for_publication(
    publication_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    return await publishing_queue_service.list_for_publication(
        session,
        publication_id,
    )


@router.post(
    "/publishing-queue/{queue_item_id}/retry",
    response_model=CFPublishingQueueItemResponse,
)
async def retry_publishing_queue_item(
    queue_item_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    try:
        item = await publishing_queue_service.retry_item(
            session,
            queue_item_id,
            actor_id=member.id,
        )
    except PublishingQueueValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Задание очереди не найдено")
    await session.commit()
    return item


@router.post(
    "/publishing-queue/{queue_item_id}/manual-fallback",
    response_model=CFPublishingQueueItemResponse,
)
async def mark_publishing_queue_manual_fallback(
    queue_item_id: uuid.UUID,
    data: CFPublishingQueueManualFallbackRequest,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    try:
        item = await publishing_queue_service.mark_manual_fallback(
            session,
            queue_item_id,
            actor_id=member.id,
            reason=data.reason,
        )
    except PublishingQueueValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Задание очереди не найдено")
    await session.commit()
    return item


@router.get(
    "/publishing-queue/{queue_item_id}/events",
    response_model=list[CFPublishingQueueEventResponse],
)
async def list_publishing_queue_events(
    queue_item_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    return await publishing_queue_service.list_events(session, queue_item_id)
