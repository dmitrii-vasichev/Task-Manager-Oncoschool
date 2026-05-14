"""Funnel templates reference endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.content_factory.deps import require_cf_access, require_cf_admin
from app.db.database import get_session
from app.db.models import CFBundle, CFFunnelTemplate, TeamMember
from app.db.schemas import (
    CFFunnelTemplateCreate,
    CFFunnelTemplateResponse,
    CFFunnelTemplateUpdate,
)

router = APIRouter(prefix="/funnel-templates", tags=["content-factory"])


@router.get("", response_model=list[CFFunnelTemplateResponse])
async def list_funnel_templates(
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
    only_active: bool = Query(default=True),
):
    stmt = select(CFFunnelTemplate).order_by(CFFunnelTemplate.code)
    if only_active:
        stmt = stmt.where(CFFunnelTemplate.is_active.is_(True))
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/{funnel_template_id}", response_model=CFFunnelTemplateResponse)
async def get_funnel_template(
    funnel_template_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    tmpl = await session.get(CFFunnelTemplate, funnel_template_id)
    if tmpl is None:
        raise HTTPException(status_code=404, detail="Шаблон воронки не найден")
    return tmpl


@router.post("", response_model=CFFunnelTemplateResponse, status_code=201)
async def create_funnel_template(
    data: CFFunnelTemplateCreate,
    member: TeamMember = Depends(require_cf_admin),
    session: AsyncSession = Depends(get_session),
):
    existing = await session.execute(
        select(CFFunnelTemplate).where(CFFunnelTemplate.code == data.code)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="Шаблон воронки с таким code уже существует",
        )
    tmpl = CFFunnelTemplate(
        code=data.code,
        name=data.name,
        description=data.description,
        template_publications=data.template_publications,
        is_active=data.is_active,
    )
    session.add(tmpl)
    await session.commit()
    await session.refresh(tmpl)
    return tmpl


@router.patch("/{funnel_template_id}", response_model=CFFunnelTemplateResponse)
async def update_funnel_template(
    funnel_template_id: uuid.UUID,
    data: CFFunnelTemplateUpdate,
    member: TeamMember = Depends(require_cf_admin),
    session: AsyncSession = Depends(get_session),
):
    tmpl = await session.get(CFFunnelTemplate, funnel_template_id)
    if tmpl is None:
        raise HTTPException(status_code=404, detail="Шаблон воронки не найден")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(tmpl, field, value)
    await session.commit()
    await session.refresh(tmpl)
    return tmpl


@router.delete("/{funnel_template_id}", status_code=204)
async def delete_funnel_template(
    funnel_template_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_admin),
    session: AsyncSession = Depends(get_session),
):
    tmpl = await session.get(CFFunnelTemplate, funnel_template_id)
    if tmpl is None:
        raise HTTPException(status_code=404, detail="Шаблон воронки не найден")
    count_result = await session.execute(
        select(func.count())
        .select_from(CFBundle)
        .where(CFBundle.funnel_template_id == funnel_template_id)
    )
    in_use = count_result.scalar_one()
    if in_use > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Шаблон воронки используется в {in_use} бандлах, удаление невозможно",
        )
    await session.delete(tmpl)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
