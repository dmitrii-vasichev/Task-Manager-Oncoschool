import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.content_factory import formats as formats_api
from app.db.schemas import CFFormatCreate, CFFormatUpdate


def cf_member(role="member", has_cf=True):
    return SimpleNamespace(
        id=uuid.uuid4(), role=role, is_active=True,
        has_content_factory_access=has_cf,
    )


def make_format(**overrides):
    base = {
        "id": uuid.uuid4(),
        "code": "button",
        "display_name": "Button",
        "default_objective": None,
        "requires_medical_review": False,
        "is_active": True,
        "display_order": 10,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_list_formats_returns_all(monkeypatch):
    session = AsyncMock()
    formats = [make_format(), make_format(code="post", display_name="Post")]

    scalars_result = MagicMock()
    scalars_result.all.return_value = formats
    exec_result = MagicMock()
    exec_result.scalars.return_value = scalars_result
    session.execute = AsyncMock(return_value=exec_result)

    result = await formats_api.list_formats(
        member=cf_member(), session=session, only_active=False
    )
    assert len(result) == 2


@pytest.mark.asyncio
async def test_create_format_requires_admin():
    non_admin = cf_member(role="member", has_cf=True)
    from app.api.content_factory.deps import require_cf_admin
    with pytest.raises(HTTPException) as exc:
        await require_cf_admin(member=non_admin)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_format_persists(monkeypatch):
    admin = cf_member(role="admin")
    session = AsyncMock()
    session.add = MagicMock()  # session.add is sync in real SQLAlchemy
    # Pre-check returns "no existing" for the dup check:
    no_existing = AsyncMock()
    no_existing.scalar_one_or_none = MagicMock(return_value=None)
    session.execute = AsyncMock(return_value=no_existing)
    data = CFFormatCreate(
        code="video",
        display_name="Video",
        default_objective="awareness",
        requires_medical_review=False,
        is_active=True,
        display_order=50,
    )

    await formats_api.create_format(
        data=data, member=admin, session=session
    )

    session.add.assert_called_once()
    added = session.add.call_args.args[0]
    assert added.code == "video"
    assert added.display_name == "Video"
    assert added.default_objective == "awareness"
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_create_format_409_when_code_exists(monkeypatch):
    admin = cf_member(role="admin")
    session = AsyncMock()
    existing = AsyncMock()
    existing.scalar_one_or_none = MagicMock(return_value=make_format())
    session.execute = AsyncMock(return_value=existing)
    data = CFFormatCreate(
        code="button",
        display_name="Button dup",
        default_objective=None,
        requires_medical_review=False,
        is_active=True,
        display_order=10,
    )

    with pytest.raises(HTTPException) as exc:
        await formats_api.create_format(
            data=data, member=admin, session=session
        )
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_update_format_404_when_missing(monkeypatch):
    admin = cf_member(role="admin")
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)
    data = CFFormatUpdate(display_name="X")
    with pytest.raises(HTTPException) as exc:
        await formats_api.update_format(
            format_id=uuid.uuid4(), data=data, member=admin, session=session
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_format_returns_204(monkeypatch):
    admin = cf_member(role="admin")
    fmt = make_format()
    session = AsyncMock()
    session.get = AsyncMock(return_value=fmt)
    # FK pre-check returns 0 (no publications use this format):
    count_result = AsyncMock()
    count_result.scalar_one = MagicMock(return_value=0)
    session.execute = AsyncMock(return_value=count_result)

    resp = await formats_api.delete_format(
        format_id=fmt.id, member=admin, session=session
    )

    assert resp.status_code == 204
    session.delete.assert_awaited_with(fmt)
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_delete_format_409_when_in_use(monkeypatch):
    admin = cf_member(role="admin")
    fmt = make_format()
    session = AsyncMock()
    session.get = AsyncMock(return_value=fmt)
    count_result = AsyncMock()
    count_result.scalar_one = MagicMock(return_value=2)
    session.execute = AsyncMock(return_value=count_result)

    with pytest.raises(HTTPException) as exc:
        await formats_api.delete_format(
            format_id=fmt.id, member=admin, session=session
        )
    assert exc.value.status_code == 409
    session.delete.assert_not_awaited()
