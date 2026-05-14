import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api import team as team_api
from app.db.schemas import TeamMemberUpdate


def make_member(*, role: str = "member", member_id: uuid.UUID | None = None):
    return SimpleNamespace(
        id=member_id or uuid.uuid4(),
        role=role,
        is_active=True,
        is_test=False,
        has_content_factory_access=False,
        telegram_id=None,
        full_name="X",
        department_id=None,
    )


@pytest.mark.asyncio
async def test_non_admin_cannot_grant_cf_access(monkeypatch):
    moderator = make_member(role="moderator")
    target = make_member(role="member")
    session = AsyncMock()
    data = TeamMemberUpdate(has_content_factory_access=True)

    monkeypatch.setattr(
        team_api.member_repo,
        "get_by_id",
        AsyncMock(return_value=target),
    )

    with pytest.raises(HTTPException) as exc:
        await team_api.update_team_member(
            member_id=target.id, data=data, member=moderator, session=session
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_grant_cf_access(monkeypatch):
    admin = make_member(role="admin")
    target = make_member(role="member")
    session = AsyncMock()
    data = TeamMemberUpdate(has_content_factory_access=True)

    monkeypatch.setattr(
        team_api.member_repo,
        "get_by_id",
        AsyncMock(return_value=target),
    )
    # Update flow ends by re-fetching and returning the updated member.
    monkeypatch.setattr(
        team_api.member_repo,
        "update",
        AsyncMock(return_value=target),
    )

    result = await team_api.update_team_member(
        member_id=target.id, data=data, member=admin, session=session
    )
    assert result is target
