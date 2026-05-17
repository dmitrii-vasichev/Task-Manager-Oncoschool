from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import settings
from app.services.content_factory.metric_source_service import MetricSourceConfigService
from app.services.content_factory.vk_metric_collector_service import (
    VKMetricCollectorService,
)


logger = logging.getLogger(__name__)


class ContentFactoryMetricImportSchedulerService:
    """Runs configured Content Factory metric imports on a schedule."""

    def __init__(
        self,
        *,
        session_maker: async_sessionmaker,
        collector: VKMetricCollectorService | None = None,
        source_config_service=MetricSourceConfigService,
        enabled: bool | None = None,
        interval_minutes: int | None = None,
    ) -> None:
        self.session_maker = session_maker
        self.collector = collector or VKMetricCollectorService()
        self.source_config_service = source_config_service
        self.enabled = settings.CF_METRIC_IMPORT_ENABLED if enabled is None else enabled
        self.interval_minutes = (
            settings.CF_METRIC_IMPORT_INTERVAL_MINUTES
            if interval_minutes is None
            else interval_minutes
        )
        self.scheduler = AsyncIOScheduler()

    def start(self) -> None:
        if not self.enabled:
            logger.info("ContentFactoryMetricImportSchedulerService disabled")
            return
        if self.scheduler.running:
            logger.info("ContentFactoryMetricImportSchedulerService already running")
            return
        self.scheduler.add_job(
            self.collect_due_sources_once,
            "interval",
            minutes=self.interval_minutes,
            id="content_factory_metric_import_scheduler",
            replace_existing=True,
        )
        self.scheduler.start()
        logger.info("ContentFactoryMetricImportSchedulerService started")

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("ContentFactoryMetricImportSchedulerService stopped")

    async def collect_due_sources_once(self) -> dict[str, int]:
        if not self.enabled:
            return {"sources": 0, "succeeded": 0, "failed": 0}

        source_count = 0
        succeeded = 0
        failed = 0
        try:
            async with self.session_maker() as session:
                sources = await self.source_config_service.list(
                    session,
                    source="vk_api",
                    is_active=True,
                    limit=100,
                    offset=0,
                )
                source_count = len(sources)
                for source_config in sources:
                    try:
                        await self.collector.collect_for_source(
                            session,
                            source_config,
                            triggered_by="scheduled",
                        )
                        succeeded += 1
                    except Exception as exc:
                        failed += 1
                        logger.error(
                            "Content Factory metric import failed source_id=%s err=%s",
                            getattr(source_config, "id", None),
                            exc,
                            exc_info=True,
                        )
                if source_count:
                    await session.commit()
        except Exception as exc:
            logger.error(
                "Content Factory metric import scheduler failed: %s",
                exc,
                exc_info=True,
            )
        return {"sources": source_count, "succeeded": succeeded, "failed": failed}
