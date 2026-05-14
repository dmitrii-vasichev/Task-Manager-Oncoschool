import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.content_factory import rubrics as rubrics_api
from app.db.schemas import CFRubricCreate, CFRubricUpdate


def cf_member(role="member", has_cf=True):
    return SimpleNamespace(
        id=uuid.uuid4(), role=role, is_active=True,
        has_content_factory_access=has_cf,
    )


def make_rubric(**overrides):
    base = {
        "id": uuid.uuid4(),
        "code": "expert",
        "display_name": "Expert",
        "is_active": True,
        "deprecated_at": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_list_rubrics_returns_all(monkeypatch):
    session = AsyncMock()
    rubrics = [make_rubric(), make_rubric(code="news", display_name="News")]

    scalars_result = MagicMock()
    scalars_result.all.return_value = rubrics
    exec_result = MagicMock()
    exec_result.scalars.return_value = scalars_result
    session.execute = AsyncMock(return_value=exec_result)

    result = await rubrics_api.list_rubrics(
        member=cf_member(), session=session, only_active=False
    )
    assert len(result) == 2


@pytest.mark.asyncio
async def test_create_rubric_requires_admin():
    non_admin = cf_member(role="member", has_cf=True)
    from app.api.content_factory.deps import require_cf_admin
    with pytest.raises(HTTPException) as exc:
        await require_cf_admin(member=non_admin)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_rubric_persists(monkeypatch):
    admin = cf_member(role="admin")
    session = AsyncMock()
    session.add = MagicMock()  # session.add is sync in real SQLAlchemy
    # Pre-check returns "no existing" for the dup check:
    no_existing = AsyncMock()
    no_existing.scalar_one_or_none = MagicMock(return_value=None)
    session.execute = AsyncMock(return_value=no_existing)
    data = CFRubricCreate(
        code="case",
        display_name="Case",
        is_active=True,
    )

    await rubrics_api.create_rubric(
        data=data, member=admin, session=session
    )

    session.add.assert_called_once()
    added = session.add.call_args.args[0]
    assert added.code == "case"
    assert added.display_name == "Case"
    assert added.is_active is True
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_create_rubric_409_when_code_exists(monkeypatch):
    admin = cf_member(role="admin")
    session = AsyncMock()
    existing = AsyncMock()
    existing.scalar_one_or_none = MagicMock(return_value=make_rubric())
    session.execute = AsyncMock(return_value=existing)
    data = CFRubricCreate(
        code="expert",
        display_name="Expert dup",
        is_active=True,
    )

    with pytest.raises(HTTPException) as exc:
        await rubrics_api.create_rubric(
            data=data, member=admin, session=session
        )
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_update_rubric_404_when_missing(monkeypatch):
    admin = cf_member(role="admin")
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)
    data = CFRubricUpdate(display_name="X")
    with pytest.raises(HTTPException) as exc:
        await rubrics_api.update_rubric(
            rubric_id=uuid.uuid4(), data=data, member=admin, session=session
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_rubric_returns_204(monkeypatch):
    admin = cf_member(role="admin")
    rubric = make_rubric()
    session = AsyncMock()
    session.get = AsyncMock(return_value=rubric)
    # FK pre-check returns 0 (no publications use this rubric):
    count_result = AsyncMock()
    count_result.scalar_one = MagicMock(return_value=0)
    session.execute = AsyncMock(return_value=count_result)

    resp = await rubrics_api.delete_rubric(
        rubric_id=rubric.id, member=admin, session=session
    )

    assert resp.status_code == 204
    session.delete.assert_awaited_with(rubric)
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_delete_rubric_409_when_in_use(monkeypatch):
    admin = cf_member(role="admin")
    rubric = make_rubric()
    session = AsyncMock()
    session.get = AsyncMock(return_value=rubric)
    count_result = AsyncMock()
    count_result.scalar_one = MagicMock(return_value=3)
    session.execute = AsyncMock(return_value=count_result)

    with pytest.raises(HTTPException) as exc:
        await rubrics_api.delete_rubric(
            rubric_id=rubric.id, member=admin, session=session
        )
    assert exc.value.status_code == 409
    session.delete.assert_not_awaited()
