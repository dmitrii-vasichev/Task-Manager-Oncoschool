"""Retro endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.content_factory.deps import require_cf_access
from app.db.database import get_session
from app.db.models import TeamMember
from app.db.schemas import (
    CFRetroNoteCreate,
    CFRetroNoteResponse,
    CFRetroNoteUpdate,
)
from app.services.content_factory.retro_service import RetroService

router = APIRouter(prefix="/retros", tags=["content-factory"])
retro_service = RetroService


@router.get("", response_model=list[CFRetroNoteResponse])
async def list_retros(
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
    retro_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
):
    return await retro_service.list(session, retro_type=retro_type, limit=limit)


@router.post("", response_model=CFRetroNoteResponse, status_code=201)
async def create_retro(
    data: CFRetroNoteCreate,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    retro = await retro_service.create(session, data)
    await session.commit()
    return retro


@router.get("/{retro_id}", response_model=CFRetroNoteResponse)
async def get_retro(
    retro_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    retro = await retro_service.get(session, retro_id)
    if retro is None:
        raise HTTPException(status_code=404, detail="Ретро не найдено")
    return retro


@router.patch("/{retro_id}", response_model=CFRetroNoteResponse)
async def update_retro(
    retro_id: uuid.UUID,
    data: CFRetroNoteUpdate,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    retro = await retro_service.update(session, retro_id, data)
    if retro is None:
        raise HTTPException(status_code=404, detail="Ретро не найдено")
    await session.commit()
    return retro
