"""Formats reference table endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.content_factory.deps import require_cf_access, require_cf_admin
from app.db.database import get_session
from app.db.models import CFFormat, CFPublication, TeamMember
from app.db.schemas import (
    CFFormatCreate,
    CFFormatResponse,
    CFFormatUpdate,
)

router = APIRouter(prefix="/formats", tags=["content-factory"])


@router.get("", response_model=list[CFFormatResponse])
async def list_formats(
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
    only_active: bool = Query(default=True),
):
    stmt = select(CFFormat).order_by(CFFormat.display_order, CFFormat.code)
    if only_active:
        stmt = stmt.where(CFFormat.is_active.is_(True))
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/{format_id}", response_model=CFFormatResponse)
async def get_format(
    format_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    fmt = await session.get(CFFormat, format_id)
    if fmt is None:
        raise HTTPException(status_code=404, detail="Формат не найден")
    return fmt


@router.post("", response_model=CFFormatResponse, status_code=201)
async def create_format(
    data: CFFormatCreate,
    member: TeamMember = Depends(require_cf_admin),
    session: AsyncSession = Depends(get_session),
):
    existing = await session.execute(
        select(CFFormat).where(CFFormat.code == data.code)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="Формат с таким code уже существует",
        )
    fmt = CFFormat(
        code=data.code,
        display_name=data.display_name,
        default_objective=data.default_objective,
        requires_medical_review=data.requires_medical_review,
        is_active=data.is_active,
        display_order=data.display_order,
    )
    session.add(fmt)
    await session.commit()
    await session.refresh(fmt)
    return fmt


@router.patch("/{format_id}", response_model=CFFormatResponse)
async def update_format(
    format_id: uuid.UUID,
    data: CFFormatUpdate,
    member: TeamMember = Depends(require_cf_admin),
    session: AsyncSession = Depends(get_session),
):
    fmt = await session.get(CFFormat, format_id)
    if fmt is None:
        raise HTTPException(status_code=404, detail="Формат не найден")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(fmt, field, value)
    await session.commit()
    await session.refresh(fmt)
    return fmt


@router.delete("/{format_id}", status_code=204)
async def delete_format(
    format_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_admin),
    session: AsyncSession = Depends(get_session),
):
    fmt = await session.get(CFFormat, format_id)
    if fmt is None:
        raise HTTPException(status_code=404, detail="Формат не найден")
    count_result = await session.execute(
        select(func.count())
        .select_from(CFPublication)
        .where(CFPublication.format_id == format_id)
    )
    in_use = count_result.scalar_one()
    if in_use > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Формат используется в {in_use} публикациях, удаление невозможно",
        )
    await session.delete(fmt)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
