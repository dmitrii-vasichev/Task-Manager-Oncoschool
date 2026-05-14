import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api.content_factory import bundles as bundles_api
from app.db.schemas import CFBundleCreate, CFBundleUpdate


def cf_member(role="member", has_cf=True):
    return SimpleNamespace(
        id=uuid.uuid4(), role=role, is_active=True,
        has_content_factory_access=has_cf,
    )


def make_bundle(**ov):
    base = {
        "id": uuid.uuid4(), "short_id": "BDL-1",
        "name": "Эфир по РМЖ", "product_stream": "onco_school",
        "status": "planning", "event_date": None, "owner_id": uuid.uuid4(),
        "brief": "Описание", "funnel_template_id": None,
        "source_material_refs": [], "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    base.update(ov)
    return SimpleNamespace(**base)


def bundle_create_data(**ov):
    base = {
        "name": "Test", "product_stream": "onco_school",
        "status": "planning", "owner_id": uuid.uuid4(),
        "brief": "X", "funnel_template_id": None,
        "source_material_refs": [],
    }
    base.update(ov)
    return CFBundleCreate(**base)


@pytest.mark.asyncio
async def test_list_bundles_filters_pass_through(monkeypatch):
    session = AsyncMock()
    listed = [make_bundle(), make_bundle(name="Second")]
    monkeypatch.setattr(
        bundles_api.bundle_service, "list",
        AsyncMock(return_value=listed),
    )

    result = await bundles_api.list_bundles(
        member=cf_member(), session=session,
        product_stream=None, status=None, owner_id=None,
        limit=100, offset=0,
    )
    assert len(result) == 2
    bundles_api.bundle_service.list.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_bundle_persists(monkeypatch):
    bundle = make_bundle()
    session = AsyncMock()
    monkeypatch.setattr(
        bundles_api.bundle_service, "create",
        AsyncMock(return_value=bundle),
    )
    result = await bundles_api.create_bundle(
        data=bundle_create_data(), member=cf_member(), session=session,
    )
    assert result is bundle
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_get_bundle_404(monkeypatch):
    session = AsyncMock()
    monkeypatch.setattr(
        bundles_api.bundle_service, "get", AsyncMock(return_value=None)
    )
    with pytest.raises(HTTPException) as exc:
        await bundles_api.get_bundle(
            bundle_id=uuid.uuid4(), member=cf_member(), session=session,
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_bundle_404(monkeypatch):
    session = AsyncMock()
    monkeypatch.setattr(
        bundles_api.bundle_service, "update", AsyncMock(return_value=None)
    )
    with pytest.raises(HTTPException) as exc:
        await bundles_api.update_bundle(
            bundle_id=uuid.uuid4(),
            data=CFBundleUpdate(name="X"),
            member=cf_member(), session=session,
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_bundle_returns_204(monkeypatch):
    session = AsyncMock()
    monkeypatch.setattr(
        bundles_api.bundle_service, "delete", AsyncMock(return_value=True)
    )
    result = await bundles_api.delete_bundle(
        bundle_id=uuid.uuid4(), member=cf_member(), session=session,
    )
    # delete_bundle returns a Response object
    assert result.status_code == 204
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_delete_bundle_404(monkeypatch):
    session = AsyncMock()
    monkeypatch.setattr(
        bundles_api.bundle_service, "delete", AsyncMock(return_value=False)
    )
    with pytest.raises(HTTPException) as exc:
        await bundles_api.delete_bundle(
            bundle_id=uuid.uuid4(), member=cf_member(), session=session,
        )
    assert exc.value.status_code == 404
