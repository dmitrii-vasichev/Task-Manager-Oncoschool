"""Bundles endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.content_factory.deps import require_cf_access
from app.db.database import get_session
from app.db.models import TeamMember
from app.db.schemas import (
    CFBundleCreate,
    CFBundleResponse,
    CFBundleUpdate,
)
from app.services.content_factory.bundle_service import BundleService

router = APIRouter(prefix="/bundles", tags=["content-factory"])
bundle_service = BundleService


@router.get("", response_model=list[CFBundleResponse])
async def list_bundles(
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
    product_stream: str | None = Query(default=None),
    status: str | None = Query(default=None),
    owner_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    return await bundle_service.list(
        session,
        product_stream=product_stream,
        status=status,
        owner_id=owner_id,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=CFBundleResponse, status_code=201)
async def create_bundle(
    data: CFBundleCreate,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    bundle = await bundle_service.create(session, data)
    await session.commit()
    return bundle


@router.get("/{bundle_id}", response_model=CFBundleResponse)
async def get_bundle(
    bundle_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    bundle = await bundle_service.get(session, bundle_id)
    if bundle is None:
        raise HTTPException(status_code=404, detail="Bundle не найден")
    return bundle


@router.patch("/{bundle_id}", response_model=CFBundleResponse)
async def update_bundle(
    bundle_id: uuid.UUID,
    data: CFBundleUpdate,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    bundle = await bundle_service.update(session, bundle_id, data)
    if bundle is None:
        raise HTTPException(status_code=404, detail="Bundle не найден")
    await session.commit()
    return bundle


@router.delete("/{bundle_id}", status_code=204)
async def delete_bundle(
    bundle_id: uuid.UUID,
    member: TeamMember = Depends(require_cf_access),
    session: AsyncSession = Depends(get_session),
):
    ok = await bundle_service.delete(session, bundle_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Bundle не найден")
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
