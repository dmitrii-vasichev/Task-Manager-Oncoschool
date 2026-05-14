"""Platforms reference table endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.content_factory.deps import require_cf_access, require_cf_admin
from app.db.database import get_session
from app.db.models import CFPlatform, CFPublication, TeamMember
from app.db.schemas import (
    CFPlatformCreate,
    CFPlatformResponse,
    CFPlatformUpdate,
)

router = APIRouter(prefix="/platforms", tags=["content-factory"])


@router.get("", response_model=list[CFPlatformResponse])
async def list_platforms(
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
    only_active: bool = Query(default=True),
):
    stmt = select(CFPlatform).order_by(CFPlatform.display_order, CFPlatform.code)
    if only_active:
        stmt = stmt.where(CFPlatform.is_active.is_(True))
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/{platform_id}", response_model=CFPlatformResponse)
async def get_platform(
    platform_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    plat = await session.get(CFPlatform, platform_id)
    if plat is None:
        raise HTTPException(status_code=404, detail="Платформа не найдена")
    return plat


@router.post("", response_model=CFPlatformResponse, status_code=201)
async def create_platform(
    data: CFPlatformCreate,
    member: TeamMember = Depends(require_cf_admin),
    session: AsyncSession = Depends(get_session),
):
    existing = await session.execute(
        select(CFPlatform).where(CFPlatform.code == data.code)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="Платформа с таким code уже существует",
        )
    plat = CFPlatform(
        code=data.code,
        display_name=data.display_name,
        is_active=data.is_active,
        capabilities=data.capabilities,
        display_order=data.display_order,
    )
    session.add(plat)
    await session.commit()
    await session.refresh(plat)
    return plat


@router.patch("/{platform_id}", response_model=CFPlatformResponse)
async def update_platform(
    platform_id: uuid.UUID,
    data: CFPlatformUpdate,
    member: TeamMember = Depends(require_cf_admin),
    session: AsyncSession = Depends(get_session),
):
    plat = await session.get(CFPlatform, platform_id)
    if plat is None:
        raise HTTPException(status_code=404, detail="Платформа не найдена")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(plat, field, value)
    await session.commit()
    await session.refresh(plat)
    return plat


@router.delete("/{platform_id}", status_code=204)
async def delete_platform(
    platform_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_admin),
    session: AsyncSession = Depends(get_session),
):
    plat = await session.get(CFPlatform, platform_id)
    if plat is None:
        raise HTTPException(status_code=404, detail="Платформа не найдена")
    count_result = await session.execute(
        select(func.count())
        .select_from(CFPublication)
        .where(CFPublication.platform_id == platform_id)
    )
    in_use = count_result.scalar_one()
    if in_use > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Платформа используется в {in_use} публикациях, удаление невозможно",
        )
    await session.delete(plat)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
