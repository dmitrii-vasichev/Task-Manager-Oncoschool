"""ReportSchedulerService — daily GetCourse data collection and cleanup via APScheduler."""

import asyncio
import logging
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LoginUrl
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import settings
from app.db.repositories import (
    AppSettingsRepository,
    DailyMetricRepository,
    TelegramTargetRepository,
)
from app.services.getcourse_service import GetCourseService

logger = logging.getLogger(__name__)

REPORT_SCHEDULE_KEY = "report_schedule"
DEFAULT_SCHEDULE = {
    "collection_time": "05:45",
    "send_time": "06:30",
    "timezone": "Europe/Moscow",
    "enabled": True,
}
CLEANUP_RETENTION_DAYS = 180
BACKFILL_PROGRESS_KEY = "backfill_progress"
BACKFILL_RESTART_ERROR = "Загрузка была прервана перезапуском сервера. Запустите заново."


class ReportSchedulerService:
    """Runs daily GetCourse data collection and sends report at separate times."""

    def __init__(self, bot: Bot, session_maker: async_sessionmaker) -> None:
        self.bot = bot
        self.session_maker = session_maker
        self.scheduler = AsyncIOScheduler()
        self.startup_id = str(uuid.uuid4())
        self._app_settings_repo = AppSettingsRepository()
        self._metrics_repo = DailyMetricRepository()
        self._target_repo = TelegramTargetRepository()
        self._getcourse_service = GetCourseService()
        self._collected_today: date | None = None
        self._sent_today: date | None = None
        self._last_collected_metric = None
        self._last_collected_date: date | None = None
        self._backfill_cancel: asyncio.Event | None = None

    def start(self) -> None:
        """Start the scheduler with collection check, send check and cleanup jobs."""
        if self.scheduler.running:
            logger.info("ReportSchedulerService already running")
            return

        self.scheduler.add_job(
            self._check_and_collect,
            "interval",
            minutes=1,
            id="report_check_and_collect",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._check_and_send,
            "interval",
            minutes=1,
            id="report_check_and_send",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._cleanup_old_metrics,
            "cron",
            hour=3,
            minute=0,
            id="report_cleanup",
            replace_existing=True,
        )
        self.scheduler.start()
        logger.info("ReportSchedulerService scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("ReportSchedulerService scheduler stopped")

    async def reschedule(self) -> None:
        """Reload settings — called after schedule update via API."""
        logger.info("ReportSchedulerService: schedule reloaded (settings updated)")

    async def _get_schedule(self) -> dict:
        """Load schedule settings from app_settings."""
        try:
            async with self.session_maker() as session:
                setting = await self._app_settings_repo.get(session, REPORT_SCHEDULE_KEY)
                if setting and isinstance(setting.value, dict):
                    val = setting.value
                    # Migrate legacy single 'time' field
                    if "collection_time" not in val:
                        old_time = val.get("time", "05:45")
                        return {
                            "collection_time": old_time,
                            "send_time": "06:30",
                            "timezone": val.get("timezone", "Europe/Moscow"),
                            "enabled": val.get("enabled", True),
                        }
                    return val
        except Exception as e:
            logger.error("Failed to load report schedule: %s", e)
        return dict(DEFAULT_SCHEDULE)

    @staticmethod
    def _parse_time(time_str: str, default_h: int = 5, default_m: int = 45) -> tuple[int, int]:
        """Parse 'HH:MM' string into (hour, minute) tuple."""
        try:
            parts = time_str.split(":")
            return int(parts[0]), int(parts[1])
        except (ValueError, IndexError, AttributeError):
            return default_h, default_m

    async def _check_and_collect(self) -> None:
        """Check if it's collection_time and trigger data collection."""
        try:
            schedule = await self._get_schedule()

            if not schedule.get("enabled", True):
                return

            tz_name = schedule.get("timezone", "Europe/Moscow")
            try:
                tz = ZoneInfo(tz_name)
            except Exception:
                tz = ZoneInfo("Europe/Moscow")

            now = datetime.now(tz)
            today = now.date()

            if self._collected_today == today:
                return

            target_hour, target_minute = self._parse_time(
                schedule.get("collection_time", "05:45"), 5, 45
            )

            if now.hour != target_hour or now.minute != target_minute:
                return

            yesterday = today - timedelta(days=1)
            logger.info("ReportScheduler: collecting metrics for %s", yesterday)

            metric = await self._getcourse_service.collect_metrics(
                self.session_maker, yesterday
            )

            self._collected_today = today
            self._last_collected_metric = metric
            self._last_collected_date = yesterday
            logger.info("ReportScheduler: collection completed for %s", yesterday)

        except Exception as e:
            logger.error("ReportScheduler: collection failed: %s", e)

    async def _check_and_send(self) -> None:
        """Check if it's send_time and send the report notification.

        If collection hasn't finished yet, wait — the notification will be
        sent as soon as collection completes (checked every minute).
        """
        try:
            schedule = await self._get_schedule()

            if not schedule.get("enabled", True):
                return

            tz_name = schedule.get("timezone", "Europe/Moscow")
            try:
                tz = ZoneInfo(tz_name)
            except Exception:
                tz = ZoneInfo("Europe/Moscow")

            now = datetime.now(tz)
            today = now.date()

            # Already sent today
            if self._sent_today == today:
                return

            target_hour, target_minute = self._parse_time(
                schedule.get("send_time", "06:30"), 6, 30
            )

            # Not yet send_time
            if now.hour < target_hour or (now.hour == target_hour and now.minute < target_minute):
                return

            # send_time has arrived (or passed) — but collection must be done first
            if self._collected_today != today:
                # Collection hasn't completed yet — wait for it
                return

            # Collection done, send the report
            metric = self._last_collected_metric
            target_date = self._last_collected_date

            if metric is None or target_date is None:
                # Fallback: read from DB
                yesterday = today - timedelta(days=1)
                async with self.session_maker() as session:
                    metric = await self._metrics_repo.get_by_date(
                        session, "getcourse", yesterday
                    )
                target_date = yesterday
                if metric is None:
                    logger.warning("ReportScheduler: no metric found for %s, skipping send", yesterday)
                    self._sent_today = today
                    return

            await self._send_report_notification(metric, target_date)
            self._sent_today = today
            self._last_collected_metric = None
            self._last_collected_date = None
            logger.info("ReportScheduler: report sent for %s", target_date)

        except Exception as e:
            logger.error("ReportScheduler: send failed: %s", e)

    async def _send_report_notification(
        self, metric, target_date: date, *, raise_on_failure: bool = False
    ) -> int:
        """Format and send Telegram notification with metrics and deltas.

        Returns the number of successfully sent messages.
        When *raise_on_failure* is True, raises RuntimeError instead of
        silently swallowing errors (used by send_now).
        """
        # Get previous day metric for delta
        prev_date = target_date - timedelta(days=1)
        prev_metric = None
        async with self.session_maker() as session:
            prev_metric = await self._metrics_repo.get_by_date(
                session, "getcourse", prev_date
            )

        text = self._format_report_message(metric, prev_metric, target_date)
        frontend_url = settings.NEXT_PUBLIC_FRONTEND_URL
        if frontend_url.startswith("https://"):
            markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="\U0001f4ca Открыть дашборд",
                    login_url=LoginUrl(url=f"{frontend_url}/reports"),
                )
            ]])
        else:
            markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="\U0001f4ca Открыть дашборд",
                    url=f"{frontend_url}/reports",
                )
            ]])

        async with self.session_maker() as session:
            targets = await self._target_repo.get_active_by_type(
                session, "report:getcourse"
            )

        if not targets:
            msg = (
                "Нет активных Telegram-целей с типом «Отчёты». "
                "Добавьте цель в Настройки → Telegram-цели."
            )
            if raise_on_failure:
                raise RuntimeError(msg)
            logger.warning("ReportScheduler: %s", msg)
            return 0

        sent = 0
        errors: list[str] = []
        for target in targets:
            try:
                await self.bot.send_message(
                    chat_id=target.chat_id,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=markup,
                    message_thread_id=target.thread_id,
                )
                sent += 1
            except Exception as e:
                logger.warning(
                    "Failed to send report to chat %s: %s", target.chat_id, e
                )
                errors.append(f"chat {target.chat_id}: {e}")

        if sent == 0 and raise_on_failure:
            raise RuntimeError(
                f"Не удалось отправить ни в один чат. Ошибки: {'; '.join(errors)}"
            )

        return sent

    @staticmethod
    def _format_report_message(metric, prev_metric, target_date: date) -> str:
        """Format the report notification message (HTML)."""

        def money_fmt(value: Decimal) -> str:
            return f"{value:,.0f}\u20bd".replace(",", " ")

        def delta_str(current: int | Decimal, previous: int | Decimal | None, is_money: bool = False) -> str:
            if previous is None:
                return ""
            diff = current - previous
            if diff > 0:
                val = money_fmt(diff) if is_money else str(diff)
                return f"  (\u2191 {val})"
            elif diff < 0:
                val = money_fmt(abs(diff)) if is_money else str(abs(diff))
                return f"  (\u2193 {val})"
            val = money_fmt(Decimal(0)) if is_money else "0"
            return f"  (\u2192 {val})"

        date_str = target_date.strftime("%d.%m.%Y")
        prev = prev_metric

        lines = [
            f"\U0001f4ca \u041e\u0442\u0447\u0451\u0442 GetCourse \u0437\u0430 {date_str}",
            "",
            f"\U0001f464 \u041d\u043e\u0432\u044b\u0435 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0438 \u2014 <b>{metric.users_count}</b>{delta_str(metric.users_count, prev.users_count if prev else None)}",
            f"\U0001f4b3 \u041f\u043b\u0430\u0442\u0435\u0436\u0435\u0439 \u2014 <b>{metric.payments_count}</b>{delta_str(metric.payments_count, prev.payments_count if prev else None)}",
            f"\U0001f4b0 \u0421\u0443\u043c\u043c\u0430 \u2014 <b>{money_fmt(metric.payments_sum)}</b>{delta_str(metric.payments_sum, prev.payments_sum if prev else None, is_money=True)}",
            f"\U0001f4e6 \u0417\u0430\u043a\u0430\u0437\u043e\u0432 \u2014 <b>{metric.orders_count}</b>{delta_str(metric.orders_count, prev.orders_count if prev else None)}",
            f"\U0001f4b0 \u0421\u0443\u043c\u043c\u0430 \u2014 <b>{money_fmt(metric.orders_sum)}</b>{delta_str(metric.orders_sum, prev.orders_sum if prev else None, is_money=True)}",
        ]

        return "\n".join(lines)

    async def send_now(self) -> date:
        """Manually send report for yesterday. Returns the date that was sent.

        Raises RuntimeError if no metric data is available for yesterday.
        """
        schedule = await self._get_schedule()
        tz_name = schedule.get("timezone", "Europe/Moscow")
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = ZoneInfo("Europe/Moscow")

        yesterday = datetime.now(tz).date() - timedelta(days=1)

        async with self.session_maker() as session:
            metric = await self._metrics_repo.get_by_date(
                session, "getcourse", yesterday
            )

        if metric is None:
            raise RuntimeError(
                f"Данные за {yesterday.strftime('%d.%m.%Y')} не найдены. "
                "Сначала соберите данные на вкладке Отчёты."
            )

        sent = await self._send_report_notification(
            metric, yesterday, raise_on_failure=True
        )
        logger.info("Manual send_now completed for %s — sent to %d chats", yesterday, sent)
        return yesterday

    async def _cleanup_old_metrics(self) -> None:
        """Delete metrics older than retention period."""
        try:
            cutoff = date.today() - timedelta(days=CLEANUP_RETENTION_DAYS)
            async with self.session_maker() as session:
                async with session.begin():
                    count = await self._metrics_repo.delete_older_than(
                        session, "getcourse", cutoff
                    )
            if count:
                logger.info("Report cleanup: deleted %d metrics older than %s", count, cutoff)
        except Exception as e:
            logger.error("Report cleanup failed: %s", e)

    def cancel_backfill(self) -> bool:
        """Signal the running backfill to stop. Returns True if a backfill was running."""
        if self._backfill_cancel and not self._backfill_cancel.is_set():
            self._backfill_cancel.set()
            logger.info("Backfill cancel requested")
            return True
        return False

    async def recover_orphaned_backfill(self) -> None:
        """Mark an in-progress backfill from an older process as failed.

        Backfill runs as an in-process background task. If Railway restarts the
        container, the task is terminated and cannot be resumed safely. On the
        next startup we convert the orphaned status into an explicit failure so
        the UI no longer shows a misleading long-running job.
        """
        try:
            async with self.session_maker() as session:
                async with session.begin():
                    setting = await self._app_settings_repo.get(session, BACKFILL_PROGRESS_KEY)
                    if not setting or not isinstance(setting.value, dict):
                        return

                    progress = setting.value
                    if progress.get("status") != "running":
                        return

                    if progress.get("startup_id") == self.startup_id:
                        return

                    now = datetime.now(tz=ZoneInfo("UTC")).isoformat()
                    previous_startup_id = progress.get("startup_id")
                    await self._app_settings_repo.set(
                        session,
                        BACKFILL_PROGRESS_KEY,
                        {
                            **progress,
                            "status": "failed",
                            "error": BACKFILL_RESTART_ERROR,
                            "interrupted_at": now,
                            "recovered_at": now,
                            "recovered_by_startup_id": self.startup_id,
                            "previous_startup_id": previous_startup_id,
                        },
                    )
            logger.warning(
                "Recovered orphaned backfill from startup %s on startup %s",
                previous_startup_id,
                self.startup_id,
            )
        except Exception:
            logger.exception("Failed to recover orphaned backfill state")

    async def run_backfill(
        self, date_from: date, date_to: date, collected_by_id=None,
        pause_seconds: int = 300,
    ) -> None:
        """Background backfill: collect metrics for the entire date range.

        Uses range-based collection — only 3 API requests to GetCourse
        (users, payments, deals) for the whole period, then groups by date.
        """
        total = (date_to - date_from).days + 1
        collected = 0
        failed = 0
        error_message = None

        # Set up cancellation flag
        self._backfill_cancel = asyncio.Event()

        logger.info("Backfill started: %s to %s (%d dates)", date_from, date_to, total)

        started_at = datetime.now(tz=ZoneInfo("UTC")).isoformat()

        async def _save_progress(progress: dict) -> None:
            """Write progress dict to app_settings (with 10s timeout)."""
            progress["last_heartbeat"] = datetime.now(tz=ZoneInfo("UTC")).isoformat()
            try:
                async with asyncio.timeout(10):
                    async with self.session_maker() as session:
                        async with session.begin():
                            await self._app_settings_repo.set(
                                session, BACKFILL_PROGRESS_KEY, progress,
                            )
            except Exception as e:
                logger.error("Failed to save backfill progress: %s", e)

        # Save "running" status at the start
        await _save_progress({
            "status": "running",
            "stage": "starting",
            "total_dates": total,
            "collected": 0,
            "failed": 0,
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "started_at": started_at,
            "startup_id": self.startup_id,
            "pause_seconds": pause_seconds,
        })

        # Non-blocking progress callback: fires DB write without blocking backfill
        async def _update_progress(event: str, detail: dict) -> None:
            progress: dict = {
                "status": "running",
                "stage": event,
                "total_dates": total,
                "collected": 0,
                "failed": 0,
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
                "started_at": started_at,
                "startup_id": self.startup_id,
                "pause_seconds": pause_seconds,
            }
            progress.update(detail)
            asyncio.create_task(_save_progress(progress))

        try:
            result = await self._getcourse_service.collect_metrics_range(
                self.session_maker, date_from, date_to, collected_by_id,
                on_progress=_update_progress,
                cancel_flag=self._backfill_cancel,
                pause_seconds=pause_seconds,
            )
            collected = result["collected"]
        except asyncio.CancelledError:
            error_message = "Отменено пользователем"
            logger.info("Backfill cancelled by user")
        except Exception as e:
            failed = total
            error_message = str(e)
            logger.error("Backfill failed: %s", e)

        # Determine final status
        if error_message == "Отменено пользователем":
            final_status = "cancelled"
        elif failed == 0:
            final_status = "completed"
        else:
            final_status = "failed"

        # Save final status (blocking — must complete before function returns)
        await _save_progress({
            "status": final_status,
            "total_dates": total,
            "collected": collected,
            "failed": failed,
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "started_at": started_at,
            "completed_at": datetime.now(tz=ZoneInfo("UTC")).isoformat(),
            "error": error_message,
            "startup_id": self.startup_id,
            "pause_seconds": pause_seconds,
        })

        self._backfill_cancel = None

        logger.info(
            "Backfill %s: total=%d, collected=%d, failed=%d",
            final_status, total, collected, failed,
        )
