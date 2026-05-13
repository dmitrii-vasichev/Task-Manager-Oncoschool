import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api import ideas as ideas_api
from app.db.schemas import IdeaCreate, IdeaStatusChange


@pytest.mark.asyncio
async def test_create_idea_returns_service_response_and_commits(monkeypatch):
    member = SimpleNamespace(id=uuid.uuid4())
    review_owner_id = uuid.uuid4()
    idea_id = uuid.uuid4()
    data = IdeaCreate(
        title="Improve reports",
        description="Add a useful summary",
        review_owner_id=review_owner_id,
        department_ids=[],
    )
    session = AsyncMock()
    created_idea = SimpleNamespace(id=idea_id)
    shaped_response = SimpleNamespace(id=idea_id)

    monkeypatch.setattr(
        ideas_api.idea_service.repo,
        "create",
        AsyncMock(return_value=created_idea),
    )
    monkeypatch.setattr(
        ideas_api.idea_service.repo,
        "add_event",
        AsyncMock(),
    )
    monkeypatch.setattr(
        ideas_api.idea_service.repo,
        "get_by_id",
        AsyncMock(return_value=created_idea),
    )
    monkeypatch.setattr(
        ideas_api.idea_service,
        "shape_response",
        AsyncMock(return_value=shaped_response),
    )

    response = await ideas_api.create_idea(
        data=data,
        member=member,
        session=session,
    )

    assert response.id == idea_id
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_change_idea_status_raises_404_when_idea_does_not_exist(monkeypatch):
    monkeypatch.setattr(
        ideas_api.idea_service.repo,
        "get_by_id",
        AsyncMock(return_value=None),
    )

    with pytest.raises(HTTPException) as exc_info:
        await ideas_api.change_idea_status(
            idea_id=uuid.uuid4(),
            data=IdeaStatusChange(status="accepted"),
            member=SimpleNamespace(id=uuid.uuid4()),
            session=AsyncMock(),
        )

    assert exc_info.value.status_code == 404
