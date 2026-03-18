"""Service for downloading Telegram channel content via Pyrofork.

Handles: per-channel locking, rate limiting, deduplication, progress callbacks.

IMPORTANT: DB sessions are opened/closed for each DB operation to avoid
holding connections idle during long Telegram API calls (Supabase PgBouncer
drops idle connections after ~60s).
"""

import asyncio
import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Coroutine

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session
from app.db.models import ContentType
from app.db.repositories import TelegramChannelRepository, TelegramContentRepository
from app.services.telegram_connection_service import TelegramConnectionService

logger = logging.getLogger(__name__)

# Rate limiting
BATCH_SIZE = 100
BATCH_DELAY_SEC = 2.0

# Max retries after FloodWait
MAX_FLOOD_RETRIES = 2

ProgressCallback = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]

# Per-channel download locks (prevent parallel downloads of the same channel)
_channel_locks: dict[uuid.UUID, asyncio.Lock] = {}


def _get_channel_lock(channel_id: uuid.UUID) -> asyncio.Lock:
    if channel_id not in _channel_locks:
        _channel_locks[channel_id] = asyncio.Lock()
    return _channel_locks[channel_id]


class TelegramDownloadService:
    """Downloads Telegram content (posts/comments) and stores in DB."""

    def __init__(self, telegram_service: TelegramConnectionService):
        self._telegram = telegram_service
        self._channel_repo = TelegramChannelRepository()
        self._content_repo = TelegramContentRepository()

    async def prepare_analysis(
        self,
        session: AsyncSession,
        channel_ids: list[uuid.UUID],
        date_from: date,
        date_to: date,
        content_type: str = "all",
    ) -> dict:
        """Calculate existing vs missing content for given channels and date range.

        Returns preparation summary with per-channel breakdown.
        """
        dt_from = datetime.combine(date_from, datetime.min.time())
        dt_to = datetime.combine(date_to, datetime.max.time())

        channels_summary = []
        total_existing = 0

        logger.info(
            "Preparing analysis: %d channels, range=%s..%s, type=%s",
            len(channel_ids), date_from, date_to, content_type,
        )

        for ch_id in channel_ids:
            channel = await self._channel_repo.get_by_id(session, ch_id)
            if not channel:
                logger.warning("Channel %s not found in DB, skipping", ch_id)
                continue

            ct_filter = None if content_type == "all" else content_type
            existing = await self._content_repo.count_by_channel_and_date_range(
                session, ch_id, dt_from, dt_to, ct_filter
            )
            total_existing += existing

            logger.info(
                "Channel '%s' (id=%s, @%s): %d existing messages in range",
                channel.display_name, ch_id, channel.username, existing,
            )

            channels_summary.append({
                "channel_id": ch_id,
                "channel_name": channel.display_name,
                "existing_count": existing,
                "estimated_missing": None,  # Can't estimate without Telegram API
            })

        # Check if Telegram is connected
        client = await self._telegram.get_client(session)
        telegram_connected = client is not None

        return {
            "channels": channels_summary,
            "total_existing": total_existing,
            "total_estimated_missing": None,
            "telegram_connected": telegram_connected,
        }

    async def download_missing(
        self,
        channel_ids: list[uuid.UUID],
        date_from: date,
        date_to: date,
        content_type: str = "all",
        progress_callback: ProgressCallback | None = None,
    ) -> dict:
        """Download missing content from Telegram channels.

        Acquires per-channel locks (raises if locked).
        Returns download results per channel.

        Uses short-lived DB sessions to avoid idle connection timeouts.
        """
        # Get Telegram client (short DB session)
        async with async_session() as session:
            client = await self._telegram.get_client(session)
        if not client:
            raise ValueError("Telegram not connected. Connect via Settings first.")

        dt_from = datetime.combine(date_from, datetime.min.time())
        dt_to = datetime.combine(date_to, datetime.max.time())

        # Load channel metadata (short DB session)
        channels = []
        async with async_session() as session:
            for ch_id in channel_ids:
                channel = await self._channel_repo.get_by_id(session, ch_id)
                if channel:
                    channels.append((ch_id, channel.username, channel.display_name, channel.id))

        results = {}
        total_downloaded = 0

        logger.info(
            "Starting download for %d channels, range=%s..%s, type=%s",
            len(channels), dt_from.date(), dt_to.date(), content_type,
        )

        for ch_id, username, display_name, db_id in channels:
            lock = _get_channel_lock(ch_id)
            if lock.locked():
                raise ChannelLockError(
                    f"Channel '{display_name}' is currently being downloaded"
                )

            async with lock:
                count = await self._download_channel(
                    client=client,
                    channel_db_id=db_id,
                    username=username,
                    display_name=display_name,
                    dt_from=dt_from,
                    dt_to=dt_to,
                    content_type=content_type,
                    progress_callback=progress_callback,
                )
                results[str(ch_id)] = count
                total_downloaded += count

        logger.info(
            "Download complete: %d total messages from %d channels",
            total_downloaded, len(channels),
        )
        return {"total_downloaded": total_downloaded, "per_channel": results}

    @staticmethod
    def _make_naive(dt: datetime | None) -> datetime | None:
        """Strip timezone info from datetime (convert to UTC if tz-aware)."""
        if dt is None:
            return None
        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    async def _download_channel(
        self,
        client,
        channel_db_id: uuid.UUID,
        username: str,
        display_name: str,
        dt_from: datetime,
        dt_to: datetime,
        content_type: str,
        progress_callback: ProgressCallback | None,
    ) -> int:
        """Download posts/comments from a single channel.

        Uses short-lived DB sessions: one for reading existing IDs,
        one per batch for inserts. No session held during Telegram API calls.
        """
        # Get existing message IDs to skip duplicates (short session)
        async with async_session() as session:
            existing_ids = await self._content_repo.get_existing_message_ids(
                session, channel_db_id, dt_from, dt_to
            )

        if progress_callback:
            await progress_callback({
                "phase": "downloading",
                "channel": display_name,
                "progress": 0,
                "detail": f"Starting download from @{username}",
            })

        clean_username = username.lstrip("@")
        messages_batch: list[dict] = []
        downloaded = 0
        skipped = 0
        seen_total = 0
        skipped_no_text = 0
        skipped_type_filter = 0

        # Use offset_date to start iteration from dt_to + 1 day instead of
        # iterating from the very latest message. This avoids scanning
        # thousands of newer messages and hitting FloodWait before reaching
        # the target date range.
        offset_date = dt_to + timedelta(days=1)

        flood_retries = 0

        while True:
            try:
                async for message in client.get_chat_history(
                    clean_username, offset_date=offset_date
                ):
                    seen_total += 1

                    # Normalize message date (Pyrofork may return tz-aware UTC)
                    msg_date = self._make_naive(message.date)

                    # Stop if message is older than our range
                    if msg_date and msg_date < dt_from:
                        break

                    # Skip if message is newer than our range (shouldn't happen
                    # with offset_date, but guard anyway)
                    if msg_date and msg_date > dt_to:
                        continue

                    # Skip if no text content
                    if not message.text and not message.caption:
                        skipped_no_text += 1
                        continue

                    # Skip duplicates
                    if message.id in existing_ids:
                        skipped += 1
                        continue

                    # Determine content type
                    msg_type = ContentType.post
                    if message.reply_to_message_id:
                        msg_type = ContentType.comment

                    # Filter by content_type
                    if content_type == "posts" and msg_type != ContentType.post:
                        skipped_type_filter += 1
                        continue
                    if content_type == "comments" and msg_type != ContentType.comment:
                        skipped_type_filter += 1
                        continue

                    text = message.text or message.caption or ""

                    messages_batch.append({
                        "channel_id": channel_db_id,
                        "telegram_message_id": message.id,
                        "content_type": msg_type,
                        "text": text,
                        "message_date": msg_date,
                    })

                    # Bulk insert when batch is full (short session per batch)
                    if len(messages_batch) >= BATCH_SIZE:
                        async with async_session() as session:
                            inserted = await self._content_repo.bulk_insert(session, messages_batch)
                            await session.commit()
                        downloaded += inserted
                        messages_batch.clear()

                        if progress_callback:
                            await progress_callback({
                                "phase": "downloading",
                                "channel": display_name,
                                "progress": downloaded,
                                "detail": f"Downloaded {downloaded} messages (skipped {skipped} duplicates)",
                            })

                        # Rate limiting (no DB session held during sleep)
                        await asyncio.sleep(BATCH_DELAY_SEC)

                # Insert remaining messages (short session)
                if messages_batch:
                    async with async_session() as session:
                        inserted = await self._content_repo.bulk_insert(session, messages_batch)
                        await session.commit()
                    downloaded += inserted
                    messages_batch.clear()

                # Iteration completed successfully — exit the retry loop
                break

            except Exception as e:
                error_name = type(e).__name__
                if "FloodWait" in error_name and flood_retries < MAX_FLOOD_RETRIES:
                    flood_retries += 1
                    wait_time = getattr(e, "value", 60)
                    logger.warning(
                        "FloodWait for channel %s (attempt %d/%d): sleeping %s seconds",
                        username, flood_retries, MAX_FLOOD_RETRIES, wait_time,
                    )
                    if progress_callback:
                        await progress_callback({
                            "phase": "downloading",
                            "channel": display_name,
                            "progress": downloaded,
                            "detail": f"Rate limited — waiting {wait_time}s (attempt {flood_retries}/{MAX_FLOOD_RETRIES})",
                        })
                    await asyncio.sleep(wait_time)
                    # Retry the entire iteration
                    continue
                else:
                    logger.error(
                        "Error downloading channel %s: %s (type=%s, seen=%d, downloaded=%d)",
                        username, e, error_name, seen_total, downloaded,
                    )
                    raise

        detail_parts = [f"{downloaded} new"]
        if skipped:
            detail_parts.append(f"{skipped} duplicates")
        if skipped_no_text:
            detail_parts.append(f"{skipped_no_text} without text")
        if skipped_type_filter:
            detail_parts.append(f"{skipped_type_filter} filtered by type")
        detail_parts.append(f"{seen_total} scanned")

        if progress_callback:
            await progress_callback({
                "phase": "downloading",
                "channel": display_name,
                "progress": downloaded,
                "detail": f"Completed: {', '.join(detail_parts)}",
            })

        logger.info(
            "Downloaded %d from @%s (no_text=%d, type_filtered=%d, duplicates=%d, scanned=%d)",
            downloaded, username, skipped_no_text, skipped_type_filter, skipped, seen_total,
        )
        return downloaded


class ChannelLockError(Exception):
    """Raised when a channel is already being downloaded."""
