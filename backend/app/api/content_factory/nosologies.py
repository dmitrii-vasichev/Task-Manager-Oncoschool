"""Nosologies reference table endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.content_factory.deps import require_cf_access, require_cf_admin
from app.db.database import get_session
from app.db.models import CFNosology, CFPublication, TeamMember
from app.db.schemas import (
    CFNosologyCreate,
    CFNosologyResponse,
    CFNosologyUpdate,
)

router = APIRouter(prefix="/nosologies", tags=["content-factory"])


@router.get("", response_model=list[CFNosologyResponse])
async def list_nosologies(
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
    only_active: bool = Query(default=True),
):
    stmt = select(CFNosology).order_by(CFNosology.code)
    if only_active:
        stmt = stmt.where(CFNosology.is_active.is_(True))
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/{nosology_id}", response_model=CFNosologyResponse)
async def get_nosology(
    nosology_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    nosology = await session.get(CFNosology, nosology_id)
    if nosology is None:
        raise HTTPException(status_code=404, detail="Нозология не найдена")
    return nosology


@router.post("", response_model=CFNosologyResponse, status_code=201)
async def create_nosology(
    data: CFNosologyCreate,
    member: TeamMember = Depends(require_cf_admin),
    session: AsyncSession = Depends(get_session),
):
    existing = await session.execute(
        select(CFNosology).where(CFNosology.code == data.code)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="Нозология с таким code уже существует",
        )
    nosology = CFNosology(
        code=data.code,
        display_name=data.display_name,
        is_active=data.is_active,
    )
    session.add(nosology)
    await session.commit()
    await session.refresh(nosology)
    return nosology


@router.patch("/{nosology_id}", response_model=CFNosologyResponse)
async def update_nosology(
    nosology_id: uuid.UUID,
    data: CFNosologyUpdate,
    member: TeamMember = Depends(require_cf_admin),
    session: AsyncSession = Depends(get_session),
):
    nosology = await session.get(CFNosology, nosology_id)
    if nosology is None:
        raise HTTPException(status_code=404, detail="Нозология не найдена")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(nosology, field, value)
    await session.commit()
    await session.refresh(nosology)
    return nosology


@router.delete("/{nosology_id}", status_code=204)
async def delete_nosology(
    nosology_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_admin),
    session: AsyncSession = Depends(get_session),
):
    nosology = await session.get(CFNosology, nosology_id)
    if nosology is None:
        raise HTTPException(status_code=404, detail="Нозология не найдена")
    count_result = await session.execute(
        select(func.count())
        .select_from(CFPublication)
        .where(CFPublication.nosology_id == nosology_id)
    )
    in_use = count_result.scalar_one()
    if in_use > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Нозология используется в {in_use} публикациях, удаление невозможно",
        )
    await session.delete(nosology)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
