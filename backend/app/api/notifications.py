import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.db.database import get_session
from app.db.models import TeamMember
from app.db.repositories import InAppNotificationRepository
from app.db.schemas import InAppNotificationListResponse, InAppNotificationResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])
notification_repo = InAppNotificationRepository()


@router.get("", response_model=InAppNotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(30, ge=1, le=100),
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    items = await notification_repo.list_for_member(
        session,
        member.id,
        unread_only=unread_only,
        limit=limit,
    )
    unread_count = await notification_repo.get_unread_count(session, member.id)
    return InAppNotificationListResponse(items=items, unread_count=unread_count)


@router.post("/{notification_id}/read", response_model=InAppNotificationResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    notification = await notification_repo.mark_read(session, member.id, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")
    await session.commit()
    return notification


@router.post("/read-all", response_model=dict)
async def mark_all_notifications_read(
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    updated = await notification_repo.mark_all_read(session, member.id)
    await session.commit()
    return {"updated": updated}
