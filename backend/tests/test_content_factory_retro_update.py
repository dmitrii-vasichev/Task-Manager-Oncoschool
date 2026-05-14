"""Integration test for RetroService.update against the dev DB."""

import uuid
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.db.database import async_session, engine
from app.db.models import TeamMember
from app.db.schemas import CFRetroNoteCreate, CFRetroNoteUpdate
from app.services.content_factory.retro_service import RetroService


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine():
    """Dispose pool before/after to handle pytest-asyncio per-loop pool binding."""
    await engine.dispose()
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_retro_update_changes_fields():
    async with async_session() as session:
        async with session.begin():
            owner_id = (
                await session.execute(select(TeamMember.id).limit(1))
            ).scalar_one()

            retro = await RetroService.create(
                session,
                CFRetroNoteCreate(
                    period_start=date(2026, 5, 1),
                    period_end=date(2026, 5, 7),
                    retro_type="weekly",
                    bundle_id=None,
                    facilitator_id=owner_id,
                    best_by_objective={},
                    broken=[],
                    learnings={},
                    decisions={},
                    actions=[],
                    notes="initial",
                ),
            )

            updated = await RetroService.update(
                session, retro.id,
                CFRetroNoteUpdate(notes="updated", learnings={"topic": "x"}),
            )
            assert updated is not None
            assert updated.notes == "updated"
            assert updated.learnings == {"topic": "x"}


@pytest.mark.asyncio
async def test_retro_update_returns_none_for_missing():
    async with async_session() as session:
        result = await RetroService.update(
            session, uuid.uuid4(), CFRetroNoteUpdate(notes="x")
        )
        assert result is None
