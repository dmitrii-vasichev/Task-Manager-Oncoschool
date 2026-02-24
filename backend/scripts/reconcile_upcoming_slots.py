import asyncio
from types import SimpleNamespace

from app.db.database import async_session
from app.services.meeting_scheduler_service import MeetingSchedulerService


async def _run() -> int:
    # Bot/Zoom are not required for slot pre-creation.
    scheduler = MeetingSchedulerService(
        bot=SimpleNamespace(send_message=None),
        session_maker=async_session,
        zoom_service=None,
    )
    return await scheduler.ensure_upcoming_slots_now()


def main() -> None:
    created = asyncio.run(_run())
    print(f"Created upcoming slots: {created}")


if __name__ == "__main__":
    main()
