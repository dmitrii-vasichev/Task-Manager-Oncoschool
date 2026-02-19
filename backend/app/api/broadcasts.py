import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_moderator
from app.db.database import get_session
from app.db.models import TeamMember
from app.db.repositories import TelegramBroadcastRepository, TelegramTargetRepository
from app.db.schemas import (
    TelegramBroadcastCreate,
    TelegramBroadcastResponse,
    TelegramBroadcastStatusType,
    TelegramBroadcastUpdate,
)

router = APIRouter(prefix="/broadcasts", tags=["broadcasts"])

broadcast_repo = TelegramBroadcastRepository()
target_repo = TelegramTargetRepository()

MAX_TELEGRAM_MESSAGE_LEN = 4096


def _to_utc_naive(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _validate_message_html(message_html: str) -> str:
    message = (message_html or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Текст сообщения не может быть пустым")
    if len(message) > MAX_TELEGRAM_MESSAGE_LEN:
        raise HTTPException(
            status_code=400,
            detail=f"Сообщение слишком длинное (максимум {MAX_TELEGRAM_MESSAGE_LEN} символов)",
        )
    return message


def _validate_scheduled_at(scheduled_at: datetime) -> datetime:
    scheduled_utc = _to_utc_naive(scheduled_at)
    if scheduled_utc < datetime.utcnow() - timedelta(minutes=1):
        raise HTTPException(
            status_code=400,
            detail="Время отправки не может быть в прошлом",
        )
    return scheduled_utc


@router.get("", response_model=list[TelegramBroadcastResponse])
async def get_broadcasts(
    status_filter: TelegramBroadcastStatusType | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=200),
    _: TeamMember = Depends(require_moderator),
    session: AsyncSession = Depends(get_session),
):
    """List scheduled/sent/failed broadcasts (moderator+)."""
    return await broadcast_repo.get_all(session, status=status_filter, limit=limit)


@router.post("", response_model=TelegramBroadcastResponse, status_code=status.HTTP_201_CREATED)
async def create_broadcast(
    data: TelegramBroadcastCreate,
    member: TeamMember = Depends(require_moderator),
    session: AsyncSession = Depends(get_session),
):
    """Create a scheduled broadcast (moderator+)."""
    target = await target_repo.get_by_id(session, data.target_id)
    if not target or not target.is_active:
        raise HTTPException(status_code=404, detail="Telegram-группа не найдена")

    broadcast = await broadcast_repo.create(
        session,
        target_id=target.id,
        chat_id=target.chat_id,
        thread_id=target.thread_id,
        target_label=target.label,
        message_html=_validate_message_html(data.message_html),
        scheduled_at=_validate_scheduled_at(data.scheduled_at),
        status="scheduled",
        created_by_id=member.id,
    )
    await session.commit()
    return broadcast


@router.patch("/{broadcast_id}", response_model=TelegramBroadcastResponse)
async def update_broadcast(
    broadcast_id: uuid.UUID,
    data: TelegramBroadcastUpdate,
    _: TeamMember = Depends(require_moderator),
    session: AsyncSession = Depends(get_session),
):
    """Update a scheduled broadcast (moderator+)."""
    broadcast = await broadcast_repo.get_by_id(session, broadcast_id)
    if not broadcast:
        raise HTTPException(status_code=404, detail="Рассылка не найдена")

    if broadcast.status != "scheduled":
        raise HTTPException(
            status_code=409,
            detail="Можно редактировать только рассылки со статусом 'scheduled'",
        )

    update_data: dict = {}

    if data.target_id is not None:
        target = await target_repo.get_by_id(session, data.target_id)
        if not target or not target.is_active:
            raise HTTPException(status_code=404, detail="Telegram-группа не найдена")
        update_data.update(
            {
                "target_id": target.id,
                "chat_id": target.chat_id,
                "thread_id": target.thread_id,
                "target_label": target.label,
            }
        )

    if data.message_html is not None:
        update_data["message_html"] = _validate_message_html(data.message_html)

    if data.scheduled_at is not None:
        update_data["scheduled_at"] = _validate_scheduled_at(data.scheduled_at)

    if update_data:
        updated = await broadcast_repo.update(session, broadcast_id, **update_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Рассылка не найдена")
        broadcast = updated
        await session.commit()

    return broadcast


@router.delete("/{broadcast_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_broadcast(
    broadcast_id: uuid.UUID,
    _: TeamMember = Depends(require_moderator),
    session: AsyncSession = Depends(get_session),
):
    """Cancel a scheduled broadcast (moderator+)."""
    broadcast = await broadcast_repo.get_by_id(session, broadcast_id)
    if not broadcast:
        raise HTTPException(status_code=404, detail="Рассылка не найдена")

    if broadcast.status != "scheduled":
        raise HTTPException(
            status_code=409,
            detail="Можно отменить только рассылки со статусом 'scheduled'",
        )

    await broadcast_repo.update(session, broadcast_id, status="cancelled")
    await session.commit()
