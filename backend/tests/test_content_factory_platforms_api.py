import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.content_factory import platforms as platforms_api
from app.db.schemas import CFPlatformCreate, CFPlatformUpdate


def cf_member(role="member", has_cf=True):
    return SimpleNamespace(
        id=uuid.uuid4(), role=role, is_active=True,
        has_content_factory_access=has_cf,
    )


def make_platform(**overrides):
    base = {
        "id": uuid.uuid4(),
        "code": "telegram",
        "display_name": "Telegram",
        "is_active": True,
        "capabilities": {"can_api_publish": True},
        "display_order": 10,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_list_platforms_returns_all(monkeypatch):
    session = AsyncMock()
    platforms = [make_platform(), make_platform(code="vk", display_name="ВКонтакте")]

    scalars_result = MagicMock()
    scalars_result.all.return_value = platforms
    exec_result = MagicMock()
    exec_result.scalars.return_value = scalars_result
    session.execute = AsyncMock(return_value=exec_result)

    result = await platforms_api.list_platforms(
        member=cf_member(), session=session, only_active=False
    )
    assert len(result) == 2


@pytest.mark.asyncio
async def test_create_platform_requires_admin():
    non_admin = cf_member(role="member", has_cf=True)
    # FastAPI dependency would 403 — we simulate the dep raising:
    from app.api.content_factory.deps import require_cf_admin
    with pytest.raises(HTTPException) as exc:
        await require_cf_admin(member=non_admin)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_platform_persists(monkeypatch):
    admin = cf_member(role="admin")
    session = AsyncMock()
    session.add = MagicMock()  # session.add is sync in real SQLAlchemy
    # Pre-check returns "no existing" for the dup check:
    no_existing = AsyncMock()
    no_existing.scalar_one_or_none = MagicMock(return_value=None)
    session.execute = AsyncMock(return_value=no_existing)
    data = CFPlatformCreate(
        code="max", display_name="MAX",
        capabilities={"can_api_publish": False},
        is_active=True, display_order=50,
    )

    await platforms_api.create_platform(
        data=data, member=admin, session=session
    )

    session.add.assert_called_once()
    added = session.add.call_args.args[0]
    assert added.code == "max"
    assert added.display_name == "MAX"
    assert added.capabilities == {"can_api_publish": False}
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_create_platform_409_when_code_exists(monkeypatch):
    admin = cf_member(role="admin")
    session = AsyncMock()
    existing = AsyncMock()
    existing.scalar_one_or_none = MagicMock(return_value=make_platform())
    session.execute = AsyncMock(return_value=existing)
    data = CFPlatformCreate(
        code="telegram", display_name="Telegram dup",
        capabilities={}, is_active=True, display_order=10,
    )

    with pytest.raises(HTTPException) as exc:
        await platforms_api.create_platform(
            data=data, member=admin, session=session
        )
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_update_platform_404_when_missing(monkeypatch):
    admin = cf_member(role="admin")
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)
    data = CFPlatformUpdate(display_name="X")
    with pytest.raises(HTTPException) as exc:
        await platforms_api.update_platform(
            platform_id=uuid.uuid4(), data=data, member=admin, session=session
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_platform_returns_204(monkeypatch):
    admin = cf_member(role="admin")
    plat = make_platform()
    session = AsyncMock()
    session.get = AsyncMock(return_value=plat)
    # FK pre-check returns 0 (no publications use this platform):
    count_result = AsyncMock()
    count_result.scalar_one = MagicMock(return_value=0)
    session.execute = AsyncMock(return_value=count_result)

    resp = await platforms_api.delete_platform(
        platform_id=plat.id, member=admin, session=session
    )

    assert resp.status_code == 204
    session.delete.assert_awaited_with(plat)
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_delete_platform_409_when_in_use(monkeypatch):
    admin = cf_member(role="admin")
    plat = make_platform()
    session = AsyncMock()
    session.get = AsyncMock(return_value=plat)
    count_result = AsyncMock()
    count_result.scalar_one = MagicMock(return_value=3)
    session.execute = AsyncMock(return_value=count_result)

    with pytest.raises(HTTPException) as exc:
        await platforms_api.delete_platform(
            platform_id=plat.id, member=admin, session=session
        )
    assert exc.value.status_code == 409
    session.delete.assert_not_awaited()
