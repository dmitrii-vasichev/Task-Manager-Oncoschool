import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.content_factory import deps as cf_deps
from app.api.content_factory import glossary as glossary_api


def member(*, role="member", has_cf=False, is_active=True):
    return SimpleNamespace(
        id=uuid.uuid4(),
        role=role,
        is_active=is_active,
        has_content_factory_access=has_cf,
    )


@pytest.mark.asyncio
async def test_require_cf_access_blocks_non_authorized():
    dep = cf_deps.require_cf_access
    with pytest.raises(HTTPException) as exc:
        await dep(member=member())
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_cf_access_allows_flagged_member():
    dep = cf_deps.require_cf_access
    m = member(has_cf=True)
    assert await dep(member=m) is m


@pytest.mark.asyncio
async def test_glossary_returns_terms_list():
    result = await glossary_api.get_glossary(member=member(has_cf=True))
    assert len(result) >= 8
    assert result[0].term  # pydantic model attr
    assert result[0].definition


@pytest.mark.asyncio
async def test_require_cf_admin_blocks_non_admin():
    dep = cf_deps.require_cf_admin
    with pytest.raises(HTTPException) as exc:
        await dep(member=member(has_cf=True))
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_cf_admin_allows_admin():
    dep = cf_deps.require_cf_admin
    m = member(role="admin")
    assert await dep(member=m) is m
