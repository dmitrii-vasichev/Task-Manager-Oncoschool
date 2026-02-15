import logging
import uuid
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo

from app.api.auth import get_current_user, require_moderator
from app.db.database import get_session
from app.db.models import Meeting, MeetingParticipant, TeamMember
from app.db.repositories import MeetingScheduleRepository, TelegramTargetRepository, TeamMemberRepository
from app.db.schemas import (
    MeetingScheduleCreate,
    MeetingScheduleResponse,
    MeetingScheduleUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meeting-schedules", tags=["meeting-schedules"])

schedule_repo = MeetingScheduleRepository()
target_repo = TelegramTargetRepository()
member_repo = TeamMemberRepository()

VALID_RECURRENCES = {"weekly", "biweekly", "monthly_last_workday"}


def _local_to_utc(time_local: str, timezone: str) -> time:
    """Convert local time string like '15:00' to UTC time."""
    local_time = time.fromisoformat(time_local)
    local_dt = datetime.combine(date.today(), local_time)
    local_dt = local_dt.replace(tzinfo=ZoneInfo(timezone))
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
    return utc_dt.time()


def _calc_next_meeting_datetime(
    day_of_week: int, time_utc: time, timezone_str: str
) -> datetime | None:
    """Calculate the next meeting datetime (naive UTC) for a given schedule.

    Iterates 0-7 days ahead, finds the first date where:
    - the meeting time converted to local timezone matches day_of_week
    - the meeting time is in the future
    """
    now_utc = datetime.now(ZoneInfo("UTC"))
    tz = ZoneInfo(timezone_str)

    for days_ahead in range(8):
        candidate_date = now_utc.date() + timedelta(days=days_ahead)
        candidate_dt = datetime.combine(candidate_date, time_utc, tzinfo=ZoneInfo("UTC"))
        candidate_local = candidate_dt.astimezone(tz)

        if candidate_local.isoweekday() == day_of_week and candidate_dt > now_utc:
            return candidate_dt.replace(tzinfo=None)  # Return naive UTC

    return None


@router.get("", response_model=list[MeetingScheduleResponse])
async def get_all_schedules(
    _: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get all meeting schedules (active and inactive)."""
    schedules = await schedule_repo.get_all_active(session)
    return schedules


@router.get("/{schedule_id}", response_model=MeetingScheduleResponse)
async def get_schedule(
    schedule_id: uuid.UUID,
    _: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a single meeting schedule by ID."""
    schedule = await schedule_repo.get_by_id(session, schedule_id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Расписание не найдено")
    return schedule


@router.post("", response_model=MeetingScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    data: MeetingScheduleCreate,
    request: Request,
    member: TeamMember = Depends(require_moderator),
    session: AsyncSession = Depends(get_session),
):
    """Create a new meeting schedule (moderator only)."""
    # Validate
    if data.day_of_week < 1 or data.day_of_week > 7:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="day_of_week должен быть от 1 (Пн) до 7 (Вс)",
        )
    if data.recurrence not in VALID_RECURRENCES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"recurrence должен быть одним из: {', '.join(VALID_RECURRENCES)}",
        )

    # Convert local time to UTC
    try:
        time_utc = _local_to_utc(data.time_local, data.timezone)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный формат времени или timezone",
        )

    # If telegram_targets is empty, use defaults from TelegramNotificationTarget table
    telegram_targets = data.telegram_targets
    if not telegram_targets:
        active_targets = await target_repo.get_all_active(session)
        telegram_targets = [
            {"chat_id": str(t.chat_id), "thread_id": t.thread_id}
            for t in active_targets
        ]

    schedule = await schedule_repo.create(
        session,
        title=data.title,
        day_of_week=data.day_of_week,
        time_utc=time_utc,
        timezone=data.timezone,
        duration_minutes=data.duration_minutes,
        recurrence=data.recurrence,
        reminder_enabled=data.reminder_enabled,
        reminder_minutes_before=data.reminder_minutes_before,
        reminder_text=data.reminder_text,
        telegram_targets=telegram_targets,
        participant_ids=data.participant_ids,
        zoom_enabled=data.zoom_enabled,
        created_by_id=member.id,
    )

    # Create the first upcoming meeting immediately so it appears in the UI
    next_meeting_date = _calc_next_meeting_datetime(
        data.day_of_week, time_utc, data.timezone
    )
    if next_meeting_date:
        zoom_data = None
        zoom_service = getattr(request.app.state, "zoom_service", None)
        if data.zoom_enabled and zoom_service:
            try:
                tz_aware = next_meeting_date.replace(tzinfo=ZoneInfo("UTC"))
                zoom_data = await zoom_service.create_meeting(
                    topic=data.title,
                    start_time=tz_aware,
                    duration=data.duration_minutes,
                    timezone=data.timezone,
                )
            except Exception as e:
                logger.warning(f"Zoom create failed for new schedule: {e}")

        meeting = Meeting(
            title=data.title,
            meeting_date=next_meeting_date,
            schedule_id=schedule.id,
            status="scheduled",
            zoom_meeting_id=str(zoom_data["id"]) if zoom_data else None,
            zoom_join_url=zoom_data.get("join_url") if zoom_data else None,
            created_by_id=member.id,
        )
        session.add(meeting)
        await session.flush()

        if data.participant_ids:
            for pid in data.participant_ids:
                session.add(MeetingParticipant(meeting_id=meeting.id, member_id=pid))

    await session.commit()
    return schedule


@router.patch("/{schedule_id}", response_model=MeetingScheduleResponse)
async def update_schedule(
    schedule_id: uuid.UUID,
    data: MeetingScheduleUpdate,
    _: TeamMember = Depends(require_moderator),
    session: AsyncSession = Depends(get_session),
):
    """Update a meeting schedule (moderator only)."""
    schedule = await schedule_repo.get_by_id(session, schedule_id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Расписание не найдено")

    update_data = data.model_dump(exclude_unset=True)

    # Validate if provided
    if "day_of_week" in update_data:
        if update_data["day_of_week"] < 1 or update_data["day_of_week"] > 7:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="day_of_week должен быть от 1 (Пн) до 7 (Вс)",
            )
    if "recurrence" in update_data:
        if update_data["recurrence"] not in VALID_RECURRENCES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"recurrence должен быть одним из: {', '.join(VALID_RECURRENCES)}",
            )

    # Convert time_local -> time_utc if provided
    if "time_local" in update_data:
        tz = update_data.get("timezone", schedule.timezone)
        try:
            update_data["time_utc"] = _local_to_utc(update_data.pop("time_local"), tz)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный формат времени или timezone",
            )
    # Remove time_local from update_data if not already removed
    update_data.pop("time_local", None)

    schedule = await schedule_repo.update(session, schedule_id, **update_data)
    await session.commit()
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: uuid.UUID,
    _: TeamMember = Depends(require_moderator),
    session: AsyncSession = Depends(get_session),
):
    """Soft-delete a meeting schedule (moderator only)."""
    schedule = await schedule_repo.get_by_id(session, schedule_id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Расписание не найдено")

    await schedule_repo.delete(session, schedule_id)
    await session.commit()
