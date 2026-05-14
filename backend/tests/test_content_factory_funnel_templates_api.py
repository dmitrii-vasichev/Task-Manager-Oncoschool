import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.content_factory import funnel_templates as funnel_templates_api
from app.db.schemas import CFFunnelTemplateCreate, CFFunnelTemplateUpdate


def cf_member(role="member", has_cf=True):
    return SimpleNamespace(
        id=uuid.uuid4(), role=role, is_active=True,
        has_content_factory_access=has_cf,
    )


def make_funnel_template(**overrides):
    base = {
        "id": uuid.uuid4(),
        "code": "standard",
        "name": "Standard funnel",
        "description": None,
        "template_publications": [],
        "is_active": True,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_list_funnel_templates_returns_all(monkeypatch):
    session = AsyncMock()
    templates = [
        make_funnel_template(),
        make_funnel_template(code="premium", name="Premium funnel"),
    ]

    scalars_result = MagicMock()
    scalars_result.all.return_value = templates
    exec_result = MagicMock()
    exec_result.scalars.return_value = scalars_result
    session.execute = AsyncMock(return_value=exec_result)

    result = await funnel_templates_api.list_funnel_templates(
        member=cf_member(), session=session, only_active=False
    )
    assert len(result) == 2


@pytest.mark.asyncio
async def test_create_funnel_template_requires_admin():
    non_admin = cf_member(role="member", has_cf=True)
    from app.api.content_factory.deps import require_cf_admin
    with pytest.raises(HTTPException) as exc:
        await require_cf_admin(member=non_admin)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_funnel_template_persists(monkeypatch):
    admin = cf_member(role="admin")
    session = AsyncMock()
    session.add = MagicMock()  # session.add is sync in real SQLAlchemy
    # Pre-check returns "no existing" for the dup check:
    no_existing = AsyncMock()
    no_existing.scalar_one_or_none = MagicMock(return_value=None)
    session.execute = AsyncMock(return_value=no_existing)
    publications = [{"day_offset": 0, "format_code": "post"}]
    data = CFFunnelTemplateCreate(
        code="launch",
        name="Launch funnel",
        description="Pre-launch content sequence",
        template_publications=publications,
        is_active=True,
    )

    await funnel_templates_api.create_funnel_template(
        data=data, member=admin, session=session
    )

    session.add.assert_called_once()
    added = session.add.call_args.args[0]
    assert added.code == "launch"
    assert added.name == "Launch funnel"
    assert added.template_publications == publications
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_create_funnel_template_409_when_code_exists(monkeypatch):
    admin = cf_member(role="admin")
    session = AsyncMock()
    existing = AsyncMock()
    existing.scalar_one_or_none = MagicMock(return_value=make_funnel_template())
    session.execute = AsyncMock(return_value=existing)
    data = CFFunnelTemplateCreate(
        code="standard",
        name="Standard dup",
        template_publications=[],
        is_active=True,
    )

    with pytest.raises(HTTPException) as exc:
        await funnel_templates_api.create_funnel_template(
            data=data, member=admin, session=session
        )
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_update_funnel_template_404_when_missing(monkeypatch):
    admin = cf_member(role="admin")
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)
    data = CFFunnelTemplateUpdate(name="X")
    with pytest.raises(HTTPException) as exc:
        await funnel_templates_api.update_funnel_template(
            funnel_template_id=uuid.uuid4(),
            data=data,
            member=admin,
            session=session,
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_funnel_template_returns_204(monkeypatch):
    admin = cf_member(role="admin")
    tmpl = make_funnel_template()
    session = AsyncMock()
    session.get = AsyncMock(return_value=tmpl)
    # FK pre-check returns 0 (no bundles use this template):
    count_result = AsyncMock()
    count_result.scalar_one = MagicMock(return_value=0)
    session.execute = AsyncMock(return_value=count_result)

    resp = await funnel_templates_api.delete_funnel_template(
        funnel_template_id=tmpl.id, member=admin, session=session
    )

    assert resp.status_code == 204
    session.delete.assert_awaited_with(tmpl)
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_delete_funnel_template_409_when_in_use(monkeypatch):
    admin = cf_member(role="admin")
    tmpl = make_funnel_template()
    session = AsyncMock()
    session.get = AsyncMock(return_value=tmpl)
    count_result = AsyncMock()
    count_result.scalar_one = MagicMock(return_value=2)
    session.execute = AsyncMock(return_value=count_result)

    with pytest.raises(HTTPException) as exc:
        await funnel_templates_api.delete_funnel_template(
            funnel_template_id=tmpl.id, member=admin, session=session
        )
    assert exc.value.status_code == 409
    assert "бандлах" in exc.value.detail
    session.delete.assert_not_awaited()
