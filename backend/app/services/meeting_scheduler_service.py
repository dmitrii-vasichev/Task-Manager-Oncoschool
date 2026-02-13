import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.models import Meeting, MeetingSchedule
from app.db.repositories import MeetingScheduleRepository

logger = logging.getLogger(__name__)


class MeetingSchedulerService:
    """
    Replaces n8n workflow. Uses APScheduler.
    Every minute checks if any schedule needs to be triggered:
    create Zoom meeting + Meeting record + send Telegram reminders.
    """

    def __init__(
        self,
        bot: Bot,
        session_maker: async_sessionmaker,
        zoom_service=None,
    ):
        self.bot = bot
        self.session_maker = session_maker
        self.zoom_service = zoom_service
        self.scheduler = AsyncIOScheduler()
        # Track: "schedule_id:date" -> True (to avoid duplicates)
        self._triggered_today: dict[str, bool] = {}

    def start(self) -> None:
        """Start the scheduler with a per-minute check."""
        self.scheduler.add_job(
            self._check_schedules,
            "interval",
            minutes=1,
            id="meeting_scheduler",
            replace_existing=True,
        )
        self.scheduler.start()
        logger.info("MeetingSchedulerService started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("MeetingSchedulerService stopped")

    async def _check_schedules(self) -> None:
        """Main loop: check all active schedules and trigger if needed."""
        try:
            now_utc = datetime.now(ZoneInfo("UTC"))
            schedule_repo = MeetingScheduleRepository()

            async with self.session_maker() as session:
                schedules = await schedule_repo.get_all_active(session)

                for schedule in schedules:
                    try:
                        if await self._should_trigger(schedule, now_utc):
                            await self._trigger_meeting(session, schedule, now_utc)
                    except Exception as e:
                        logger.error(
                            f"Error processing schedule {schedule.id} ({schedule.title}): {e}"
                        )
        except Exception as e:
            logger.error(f"Error in _check_schedules: {e}")

        # Cleanup old triggered entries (keep only today)
        today = datetime.now(ZoneInfo("UTC")).date()
        self._triggered_today = {
            k: v for k, v in self._triggered_today.items()
            if k.endswith(str(today))
        }

    async def _should_trigger(self, schedule: MeetingSchedule, now_utc: datetime) -> bool:
        """Check all conditions for triggering a schedule."""
        if not schedule.reminder_enabled:
            return False

        # 1. Day of week
        current_dow = now_utc.isoweekday()  # 1=Mon
        if schedule.day_of_week != current_dow:
            return False

        # 2. Recurrence
        if schedule.recurrence == "biweekly":
            week_number = now_utc.isocalendar()[1]
            if week_number % 2 != 0:
                return False
        elif schedule.recurrence == "monthly_last_workday":
            if not self._is_last_workday_friday(now_utc):
                return False

        # 3. Time: trigger at (time_utc - reminder_minutes_before)
        trigger_time = self._calc_trigger_time(schedule)
        current_minutes = now_utc.hour * 60 + now_utc.minute
        trigger_minutes = trigger_time.hour * 60 + trigger_time.minute
        diff = abs(current_minutes - trigger_minutes)
        # Handle midnight wrap
        if diff > 720:
            diff = 1440 - diff
        if diff > 1:
            return False

        # 4. Already triggered today?
        key = f"{schedule.id}:{now_utc.date()}"
        if key in self._triggered_today:
            return False

        return True

    def _calc_trigger_time(self, schedule: MeetingSchedule) -> time:
        """Calculate trigger time = time_utc - reminder_minutes_before."""
        meeting_minutes = schedule.time_utc.hour * 60 + schedule.time_utc.minute
        trigger_minutes = meeting_minutes - schedule.reminder_minutes_before
        # Handle negative (wraps to previous day — but we only trigger on matching day)
        if trigger_minutes < 0:
            trigger_minutes += 1440
        h = trigger_minutes // 60
        m = trigger_minutes % 60
        return time(h, m)

    @staticmethod
    def _is_last_workday_friday(dt: datetime) -> bool:
        """Check: current day is Friday and it's the last Friday of the month."""
        if dt.weekday() != 4:  # 4 = Friday
            return False
        next_friday = dt + timedelta(days=7)
        return next_friday.month != dt.month

    async def _trigger_meeting(
        self,
        session,
        schedule: MeetingSchedule,
        now_utc: datetime,
    ) -> None:
        """Create Zoom meeting + Meeting record + send Telegram reminders."""
        meeting_date = self._next_meeting_datetime(schedule, now_utc)

        # 1. Create Zoom meeting (if configured)
        zoom_data = None
        if schedule.zoom_enabled and self.zoom_service:
            try:
                zoom_data = await self.zoom_service.create_meeting(
                    topic=schedule.title,
                    start_time=meeting_date,
                    duration=schedule.duration_minutes,
                    timezone=schedule.timezone,
                )
                logger.info(
                    f"Zoom meeting created for schedule '{schedule.title}': {zoom_data.get('id')}"
                )
            except Exception as e:
                logger.error(f"Zoom create failed for schedule {schedule.id}: {e}")

        # 2. Create Meeting in DB
        async with session.begin():
            meeting = Meeting(
                title=schedule.title,
                meeting_date=meeting_date,
                schedule_id=schedule.id,
                status="scheduled",
                zoom_meeting_id=str(zoom_data["id"]) if zoom_data else None,
                zoom_join_url=zoom_data.get("join_url") if zoom_data else None,
                created_by_id=schedule.created_by_id,
            )
            session.add(meeting)

        logger.info(
            f"Meeting record created for schedule '{schedule.title}' at {meeting_date}"
        )

        # 3. Send Telegram reminders
        await self._send_reminders(schedule, meeting, zoom_data)

        # 4. Mark as triggered
        key = f"{schedule.id}:{now_utc.date()}"
        self._triggered_today[key] = True

    def _next_meeting_datetime(self, schedule: MeetingSchedule, now_utc: datetime) -> datetime:
        """Calculate the meeting datetime (UTC-aware) for today's trigger."""
        meeting_dt = datetime.combine(now_utc.date(), schedule.time_utc)
        return meeting_dt.replace(tzinfo=ZoneInfo("UTC"))

    async def _send_reminders(self, schedule: MeetingSchedule, meeting: Meeting, zoom_data) -> None:
        """Send reminders to all telegram_targets."""
        text = schedule.reminder_text or self._default_reminder_text(schedule, meeting)

        if zoom_data and zoom_data.get("join_url"):
            text += f"\n\nСсылка для подключения: {zoom_data['join_url']}"

        for target in schedule.telegram_targets or []:
            chat_id = target.get("chat_id")
            thread_id = target.get("thread_id")
            if not chat_id:
                continue
            try:
                kwargs = {"chat_id": int(chat_id), "text": text, "parse_mode": "HTML"}
                if thread_id:
                    kwargs["message_thread_id"] = int(thread_id)
                await self.bot.send_message(**kwargs)
                logger.info(f"Reminder sent to chat {chat_id} for '{schedule.title}'")
            except Exception as e:
                logger.error(f"Failed to send reminder to {chat_id}: {e}")

    @staticmethod
    def _default_reminder_text(schedule: MeetingSchedule, meeting: Meeting) -> str:
        """Default reminder text if reminder_text is not set."""
        try:
            local_time = meeting.meeting_date.astimezone(ZoneInfo(schedule.timezone))
            time_str = local_time.strftime("%H:%M")
        except Exception:
            time_str = schedule.time_utc.strftime("%H:%M")

        return (
            f"Доброго времени ❤️\n\n"
            f"Напоминаем, сегодня в {time_str} по МСК "
            f"{schedule.title.lower()}"
        )
