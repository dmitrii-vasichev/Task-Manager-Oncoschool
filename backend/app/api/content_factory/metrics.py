"""Metric snapshot endpoints, mounted under /publications."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.content_factory.deps import require_cf_access
from app.db.database import get_session
from app.db.models import TeamMember
from app.db.schemas import CFMetricSnapshotCreate, CFMetricSnapshotResponse
from app.services.content_factory.metric_service import MetricService

router = APIRouter(prefix="/publications", tags=["content-factory"])
metric_service = MetricService


@router.post(
    "/{publication_id}/metrics",
    response_model=CFMetricSnapshotResponse,
    status_code=201,
)
async def record_metric(
    publication_id: uuid.UUID,
    data: CFMetricSnapshotCreate,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    # URL is the source of truth for publication_id; captured_by_id
    # is set from the JWT member.
    payload = data.model_copy(update={
        "publication_id": publication_id,
        "captured_by_id": member.id,
    })
    snap = await metric_service.record(session, payload)
    await session.commit()
    return snap


@router.get(
    "/{publication_id}/metrics",
    response_model=list[CFMetricSnapshotResponse],
)
async def list_metrics(
    publication_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    return await metric_service.list_for_publication(session, publication_id)
