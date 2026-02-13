import asyncio
import logging

import uvicorn
from aiogram import Bot, Dispatcher
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.bot.handlers.common import router as common_router
from app.bot.handlers.meetings import router as meetings_router
from app.bot.handlers.settings import router as settings_router
from app.bot.handlers.summary import router as summary_router
from app.bot.handlers.task_updates import router as task_updates_router
from app.bot.handlers.tasks import router as tasks_router
from app.bot.handlers.voice import router as voice_router
from app.bot.middlewares import AuthMiddleware
from app.config import settings
from app.db.database import async_session
from app.services.meeting_scheduler_service import MeetingSchedulerService
from app.services.reminder_service import ReminderService
from app.services.zoom_service import ZoomService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Oncoschool Task Manager", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API
app.include_router(api_router)

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Bot Middleware
dp.message.middleware(AuthMiddleware())
dp.callback_query.middleware(AuthMiddleware())

# Bot Роутеры
dp.include_router(common_router)
dp.include_router(tasks_router)
dp.include_router(task_updates_router)
dp.include_router(summary_router)
dp.include_router(voice_router)
dp.include_router(settings_router)
dp.include_router(meetings_router)

# Zoom Service (optional — graceful fallback if not configured)
zoom_service = None
if settings.zoom_configured:
    zoom_service = ZoomService(
        account_id=settings.ZOOM_ACCOUNT_ID,
        client_id=settings.ZOOM_CLIENT_ID,
        client_secret=settings.ZOOM_CLIENT_SECRET,
    )
    logger.info("ZoomService initialized")
else:
    logger.info("Zoom not configured — ZoomService disabled")

# Make zoom_service accessible from API endpoints via app.state
app.state.zoom_service = zoom_service

# Schedulers
reminder_service = ReminderService(bot=bot, session_maker=async_session)
meeting_scheduler = MeetingSchedulerService(
    bot=bot, session_maker=async_session, zoom_service=zoom_service
)


@app.get("/health")
async def health():
    return {"status": "ok"}


async def start_bot():
    """Запуск Telegram-бота в режиме polling."""
    logger.info("Starting Telegram bot polling...")
    await dp.start_polling(bot)


async def start_api():
    """Запуск FastAPI через uvicorn."""
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
    server = uvicorn.Server(config)
    logger.info("Starting FastAPI server on port 8000...")
    await server.serve()


async def main():
    """Запуск FastAPI + aiogram polling + APScheduler параллельно."""
    # Start schedulers
    reminder_service.start()
    logger.info("Reminder scheduler started")
    meeting_scheduler.start()
    logger.info("Meeting scheduler started")

    try:
        await asyncio.gather(
            start_bot(),
            start_api(),
        )
    finally:
        reminder_service.stop()
        meeting_scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())
