import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.content_factory import nosologies as nosologies_api
from app.db.schemas import CFNosologyCreate, CFNosologyUpdate


def cf_member(role="member", has_cf=True):
    return SimpleNamespace(
        id=uuid.uuid4(), role=role, is_active=True,
        has_content_factory_access=has_cf,
    )


def make_nosology(**overrides):
    base = {
        "id": uuid.uuid4(),
        "code": "lung",
        "display_name": "Lung cancer",
        "is_active": True,
        "deprecated_at": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_list_nosologies_returns_all(monkeypatch):
    session = AsyncMock()
    nosologies = [make_nosology(), make_nosology(code="breast", display_name="Breast cancer")]

    scalars_result = MagicMock()
    scalars_result.all.return_value = nosologies
    exec_result = MagicMock()
    exec_result.scalars.return_value = scalars_result
    session.execute = AsyncMock(return_value=exec_result)

    result = await nosologies_api.list_nosologies(
        member=cf_member(), session=session, only_active=False
    )
    assert len(result) == 2


@pytest.mark.asyncio
async def test_create_nosology_requires_admin():
    non_admin = cf_member(role="member", has_cf=True)
    from app.api.content_factory.deps import require_cf_admin
    with pytest.raises(HTTPException) as exc:
        await require_cf_admin(member=non_admin)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_nosology_persists(monkeypatch):
    admin = cf_member(role="admin")
    session = AsyncMock()
    session.add = MagicMock()  # session.add is sync in real SQLAlchemy
    # Pre-check returns "no existing" for the dup check:
    no_existing = AsyncMock()
    no_existing.scalar_one_or_none = MagicMock(return_value=None)
    session.execute = AsyncMock(return_value=no_existing)
    data = CFNosologyCreate(
        code="colon",
        display_name="Colon cancer",
        is_active=True,
    )

    await nosologies_api.create_nosology(
        data=data, member=admin, session=session
    )

    session.add.assert_called_once()
    added = session.add.call_args.args[0]
    assert added.code == "colon"
    assert added.display_name == "Colon cancer"
    assert added.is_active is True
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_create_nosology_409_when_code_exists(monkeypatch):
    admin = cf_member(role="admin")
    session = AsyncMock()
    existing = AsyncMock()
    existing.scalar_one_or_none = MagicMock(return_value=make_nosology())
    session.execute = AsyncMock(return_value=existing)
    data = CFNosologyCreate(
        code="lung",
        display_name="Lung dup",
        is_active=True,
    )

    with pytest.raises(HTTPException) as exc:
        await nosologies_api.create_nosology(
            data=data, member=admin, session=session
        )
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_update_nosology_404_when_missing(monkeypatch):
    admin = cf_member(role="admin")
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)
    data = CFNosologyUpdate(display_name="X")
    with pytest.raises(HTTPException) as exc:
        await nosologies_api.update_nosology(
            nosology_id=uuid.uuid4(), data=data, member=admin, session=session
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_nosology_returns_204(monkeypatch):
    admin = cf_member(role="admin")
    nosology = make_nosology()
    session = AsyncMock()
    session.get = AsyncMock(return_value=nosology)
    # FK pre-check returns 0 (no publications use this nosology):
    count_result = AsyncMock()
    count_result.scalar_one = MagicMock(return_value=0)
    session.execute = AsyncMock(return_value=count_result)

    resp = await nosologies_api.delete_nosology(
        nosology_id=nosology.id, member=admin, session=session
    )

    assert resp.status_code == 204
    session.delete.assert_awaited_with(nosology)
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_delete_nosology_409_when_in_use(monkeypatch):
    admin = cf_member(role="admin")
    nosology = make_nosology()
    session = AsyncMock()
    session.get = AsyncMock(return_value=nosology)
    count_result = AsyncMock()
    count_result.scalar_one = MagicMock(return_value=4)
    session.execute = AsyncMock(return_value=count_result)

    with pytest.raises(HTTPException) as exc:
        await nosologies_api.delete_nosology(
            nosology_id=nosology.id, member=admin, session=session
        )
    assert exc.value.status_code == 409
    session.delete.assert_not_awaited()
