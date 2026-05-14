"""Segments endpoints — read-only mirror of GetCourse segments with refresh."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.content_factory.deps import require_cf_access
from app.db.database import get_session
from app.db.models import TeamMember
from app.db.schemas import (
    CFExternalSegmentCreate,
    CFExternalSegmentResponse,
    CFSegmentRefreshRequest,
    CFSegmentSnapshotResponse,
)
from app.services.content_factory.segment_service import SegmentService

router = APIRouter(prefix="/segments", tags=["content-factory"])
segment_service = SegmentService


@router.get("", response_model=list[CFExternalSegmentResponse])
async def list_segments(
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
    only_active: bool = Query(default=True),
):
    return await segment_service.list(session, only_active=only_active)


@router.post("", response_model=CFExternalSegmentResponse, status_code=201)
async def create_segment(
    data: CFExternalSegmentCreate,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    seg = await segment_service.create(session, data)
    await session.commit()
    return seg


@router.get("/{segment_id}", response_model=CFExternalSegmentResponse)
async def get_segment(
    segment_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    seg = await segment_service.get(session, segment_id)
    if seg is None:
        raise HTTPException(status_code=404, detail="Сегмент не найден")
    return seg


@router.post("/{segment_id}/refresh", response_model=CFExternalSegmentResponse)
async def refresh_segment(
    segment_id: uuid.UUID,
    data: CFSegmentRefreshRequest,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    seg = await segment_service.refresh_population(
        session, segment_id, data.population_count
    )
    if seg is None:
        raise HTTPException(status_code=404, detail="Сегмент не найден")
    await session.commit()
    return seg


@router.get(
    "/{segment_id}/snapshots",
    response_model=list[CFSegmentSnapshotResponse],
)
async def list_segment_snapshots(
    segment_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    return await segment_service.list_snapshots(session, segment_id)
