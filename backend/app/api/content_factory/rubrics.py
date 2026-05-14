"""Rubrics reference table endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.content_factory.deps import require_cf_access, require_cf_admin
from app.db.database import get_session
from app.db.models import CFPublication, CFRubric, TeamMember
from app.db.schemas import (
    CFRubricCreate,
    CFRubricResponse,
    CFRubricUpdate,
)

router = APIRouter(prefix="/rubrics", tags=["content-factory"])


@router.get("", response_model=list[CFRubricResponse])
async def list_rubrics(
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
    only_active: bool = Query(default=True),
):
    stmt = select(CFRubric).order_by(CFRubric.code)
    if only_active:
        stmt = stmt.where(CFRubric.is_active.is_(True))
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/{rubric_id}", response_model=CFRubricResponse)
async def get_rubric(
    rubric_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    rubric = await session.get(CFRubric, rubric_id)
    if rubric is None:
        raise HTTPException(status_code=404, detail="Рубрика не найдена")
    return rubric


@router.post("", response_model=CFRubricResponse, status_code=201)
async def create_rubric(
    data: CFRubricCreate,
    member: TeamMember = Depends(require_cf_admin),
    session: AsyncSession = Depends(get_session),
):
    existing = await session.execute(
        select(CFRubric).where(CFRubric.code == data.code)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="Рубрика с таким code уже существует",
        )
    rubric = CFRubric(
        code=data.code,
        display_name=data.display_name,
        is_active=data.is_active,
    )
    session.add(rubric)
    await session.commit()
    await session.refresh(rubric)
    return rubric


@router.patch("/{rubric_id}", response_model=CFRubricResponse)
async def update_rubric(
    rubric_id: uuid.UUID,
    data: CFRubricUpdate,
    member: TeamMember = Depends(require_cf_admin),
    session: AsyncSession = Depends(get_session),
):
    rubric = await session.get(CFRubric, rubric_id)
    if rubric is None:
        raise HTTPException(status_code=404, detail="Рубрика не найдена")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rubric, field, value)
    await session.commit()
    await session.refresh(rubric)
    return rubric


@router.delete("/{rubric_id}", status_code=204)
async def delete_rubric(
    rubric_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_admin),
    session: AsyncSession = Depends(get_session),
):
    rubric = await session.get(CFRubric, rubric_id)
    if rubric is None:
        raise HTTPException(status_code=404, detail="Рубрика не найдена")
    count_result = await session.execute(
        select(func.count())
        .select_from(CFPublication)
        .where(CFPublication.rubric_id == rubric_id)
    )
    in_use = count_result.scalar_one()
    if in_use > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Рубрика используется в {in_use} публикациях, удаление невозможно",
        )
    await session.delete(rubric)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
