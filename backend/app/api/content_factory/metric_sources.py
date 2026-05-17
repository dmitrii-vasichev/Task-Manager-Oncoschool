"""Metric source configuration and import run endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.content_factory.deps import require_cf_access
from app.db.database import get_session
from app.db.models import TeamMember
from app.db.schemas import (
    CFMetricImportRunResponse,
    CFMetricSourceConfigCreate,
    CFMetricSourceConfigResponse,
    CFMetricSourceRunRequest,
    CFMetricSourceConfigUpdate,
)
from app.services.content_factory.metric_source_service import (
    MetricImportRunService,
    MetricSourceConfigService,
    MetricSourceValidationError,
)
from app.services.content_factory.vk_metric_collector_service import (
    VKMetricCollectorError,
    VKMetricCollectorService,
)

router = APIRouter(tags=["content-factory"])
source_config_service = MetricSourceConfigService
import_run_service = MetricImportRunService
vk_metric_collector = VKMetricCollectorService()


def _validation_error(exc: MetricSourceValidationError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/metric-sources",
    response_model=list[CFMetricSourceConfigResponse],
)
async def list_metric_sources(
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
    source: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    return await source_config_service.list(
        session,
        source=source,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/metric-sources",
    response_model=CFMetricSourceConfigResponse,
    status_code=201,
)
async def create_metric_source(
    data: CFMetricSourceConfigCreate,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    payload = data.model_copy(update={"created_by_id": member.id})
    try:
        source = await source_config_service.create(session, payload)
    except MetricSourceValidationError as exc:
        raise _validation_error(exc) from exc
    await session.commit()
    return source


@router.get(
    "/metric-sources/{source_config_id}",
    response_model=CFMetricSourceConfigResponse,
)
async def get_metric_source(
    source_config_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    source = await source_config_service.get(session, source_config_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Источник метрик не найден")
    return source


@router.patch(
    "/metric-sources/{source_config_id}",
    response_model=CFMetricSourceConfigResponse,
)
async def update_metric_source(
    source_config_id: uuid.UUID,
    data: CFMetricSourceConfigUpdate,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    try:
        source = await source_config_service.update(
            session,
            source_config_id,
            data,
        )
    except MetricSourceValidationError as exc:
        raise _validation_error(exc) from exc
    if source is None:
        raise HTTPException(status_code=404, detail="Источник метрик не найден")
    await session.commit()
    return source


@router.get(
    "/metric-import-runs",
    response_model=list[CFMetricImportRunResponse],
)
async def list_metric_import_runs(
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
    source_config_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    return await import_run_service.list_runs(
        session,
        source_config_id=source_config_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/metric-sources/{source_config_id}/run",
    response_model=CFMetricImportRunResponse,
)
async def run_metric_source(
    source_config_id: uuid.UUID,
    data: CFMetricSourceRunRequest,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    if data.force:
        raise HTTPException(
            status_code=400,
            detail="force mode is not supported yet",
        )

    source = await source_config_service.get(session, source_config_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Источник метрик не найден")
    if source.source != "vk_api":
        raise HTTPException(
            status_code=400,
            detail="Автосбор метрик пока поддерживает только VK API",
        )

    try:
        run = await vk_metric_collector.collect_for_source(
            session,
            source,
            triggered_by="manual",
            requested_by_id=member.id,
            publication_id=data.publication_id,
        )
    except VKMetricCollectorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await session.commit()
    return run


@router.get(
    "/metric-sources/{source_config_id}/import-runs",
    response_model=list[CFMetricImportRunResponse],
)
async def list_metric_source_import_runs(
    source_config_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    return await import_run_service.list_runs(
        session,
        source_config_id=source_config_id,
        status=status,
        limit=limit,
        offset=offset,
    )
