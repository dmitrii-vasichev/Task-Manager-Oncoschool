import logging
from datetime import datetime

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.repositories import TelegramBroadcastRepository

logger = logging.getLogger(__name__)


class BroadcastSchedulerService:
    """Dispatches scheduled Telegram broadcasts."""

    def __init__(self, bot: Bot, session_maker: async_sessionmaker):
        self.bot = bot
        self.session_maker = session_maker
        self.scheduler = AsyncIOScheduler()
        self.broadcast_repo = TelegramBroadcastRepository()

    def start(self) -> None:
        if self.scheduler.running:
            logger.info("BroadcastSchedulerService already running")
            return

        self.scheduler.add_job(
            self._send_due_broadcasts,
            "interval",
            minutes=1,
            id="telegram_broadcast_scheduler",
            replace_existing=True,
        )
        self.scheduler.start()
        logger.info("BroadcastSchedulerService started")

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("BroadcastSchedulerService stopped")

    async def _send_due_broadcasts(self) -> None:
        try:
            now_utc = datetime.utcnow()
            async with self.session_maker() as session:
                due = await self.broadcast_repo.get_due_scheduled(
                    session,
                    now_utc=now_utc,
                    limit=50,
                )
                if not due:
                    return

                for broadcast in due:
                    try:
                        kwargs = {
                            "chat_id": int(broadcast.chat_id),
                            "text": broadcast.message_html,
                            "parse_mode": "HTML",
                        }
                        if broadcast.thread_id:
                            kwargs["message_thread_id"] = int(broadcast.thread_id)

                        await self.bot.send_message(**kwargs)
                        broadcast.status = "sent"
                        broadcast.sent_at = datetime.utcnow()
                        broadcast.error_message = None
                        logger.info(
                            "Broadcast sent id=%s chat=%s",
                            broadcast.id,
                            broadcast.chat_id,
                        )
                    except Exception as e:
                        broadcast.status = "failed"
                        broadcast.error_message = str(e)[:1000]
                        logger.error(
                            "Broadcast failed id=%s chat=%s err=%s",
                            broadcast.id,
                            broadcast.chat_id,
                            e,
                        )

                await session.commit()
        except Exception as e:
            logger.error("Error in BroadcastSchedulerService: %s", e, exc_info=True)
