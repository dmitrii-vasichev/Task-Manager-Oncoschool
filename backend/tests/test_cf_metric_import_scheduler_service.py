from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.content_factory.metric_import_scheduler_service import (
    ContentFactoryMetricImportSchedulerService,
)


@pytest.mark.asyncio
async def test_metric_import_scheduler_collects_active_vk_sources():
    source = SimpleNamespace(id="source-1", source="vk_api")
    session = AsyncMock()
    source_config_service = SimpleNamespace(list=AsyncMock(return_value=[source]))
    collector = SimpleNamespace(collect_for_source=AsyncMock())

    class SessionContext:
        async def __aenter__(self):
            return session

        async def __aexit__(self, exc_type, exc, tb):
            return None

    scheduler = ContentFactoryMetricImportSchedulerService(
        session_maker=lambda: SessionContext(),
        collector=collector,
        source_config_service=source_config_service,
        enabled=True,
    )

    await scheduler.collect_due_sources_once()

    collector.collect_for_source.assert_awaited_once_with(
        session,
        source,
        triggered_by="scheduled",
    )


@pytest.mark.asyncio
async def test_metric_import_scheduler_does_nothing_when_disabled():
    source_config_service = SimpleNamespace(list=AsyncMock())
    collector = SimpleNamespace(collect_for_source=AsyncMock())
    scheduler = ContentFactoryMetricImportSchedulerService(
        session_maker=lambda: None,
        collector=collector,
        source_config_service=source_config_service,
        enabled=False,
    )

    await scheduler.collect_due_sources_once()

    source_config_service.list.assert_not_called()
    collector.collect_for_source.assert_not_called()
