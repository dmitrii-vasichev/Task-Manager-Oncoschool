"""Integration test against the live dev DB.

These tests need a real DB — the existing cf_smoke_test.py uses the same approach.
The async_session fixture connects to the Docker dev container on :5434.
Unique UUIDs in source_segment_id keep re-runs free of conflicts.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.db.database import async_session, engine
from app.db.models import (
    CFBundle,
    CFFormat,
    CFPlatform,
    TeamMember,
)
from app.db.schemas import (
    CFExternalSegmentCreate,
    CFPublicationCreate,
)
from app.services.content_factory.publication_service import PublicationService
from app.services.content_factory.segment_service import SegmentService


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_pool():
    """Each pytest-asyncio test runs in a fresh event loop, but the module-level
    engine's connection pool is bound to the first loop. Dispose before each test
    so connections are re-created on the current loop.
    """
    await engine.dispose()
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_list_versions_returns_creation_version():
    async with async_session() as session:
        async with session.begin():
            platform_id = (
                await session.execute(select(CFPlatform.id).limit(1))
            ).scalar_one()
            format_id = (
                await session.execute(select(CFFormat.id).limit(1))
            ).scalar_one()
            owner_id = (
                await session.execute(select(TeamMember.id).limit(1))
            ).scalar_one()

            bundle = CFBundle(
                name="Test bundle for versions",
                product_stream="onco_school",
                status="planning",
                owner_id=owner_id,
                brief="test",
                source_material_refs=[],
            )
            session.add(bundle)
            await session.flush()

            pub = await PublicationService.create(
                session,
                CFPublicationCreate(
                    bundle_id=bundle.id,
                    platform_id=platform_id,
                    format_id=format_id,
                    rubric_id=None,
                    nosology_id=None,
                    title="t",
                    body_text="hello",
                    media_refs=[],
                    scheduled_at=None,
                    responsible_id=owner_id,
                    status="draft",
                    utm={},
                ),
                editor_id=owner_id,
            )

            versions = await PublicationService.list_versions(session, pub.id)
            assert len(versions) == 1
            assert versions[0].version_number == 1
            assert versions[0].approval_event == "drafted"


@pytest.mark.asyncio
async def test_segment_target_attach_and_detach():
    async with async_session() as session:
        async with session.begin():
            owner_id = (
                await session.execute(select(TeamMember.id).limit(1))
            ).scalar_one()
            platform_id = (
                await session.execute(select(CFPlatform.id).limit(1))
            ).scalar_one()
            format_id = (
                await session.execute(select(CFFormat.id).limit(1))
            ).scalar_one()

            seg = await SegmentService.create(
                session,
                CFExternalSegmentCreate(
                    source="getcourse",
                    source_segment_id=f"test-{uuid.uuid4()}",
                    source_url="https://x",
                    name="Тестовый сегмент",
                    description=None,
                    population_count=1000,
                    is_active=True,
                    owner_id=owner_id,
                ),
            )

            bundle = CFBundle(
                name="B",
                product_stream="onco_school",
                status="planning",
                owner_id=owner_id,
                brief="b",
                source_material_refs=[],
            )
            session.add(bundle)
            await session.flush()
            pub = await PublicationService.create(
                session,
                CFPublicationCreate(
                    bundle_id=bundle.id,
                    platform_id=platform_id,
                    format_id=format_id,
                    rubric_id=None,
                    nosology_id=None,
                    title="t",
                    body_text="b",
                    media_refs=[],
                    scheduled_at=None,
                    responsible_id=owner_id,
                    status="draft",
                    utm={},
                ),
                editor_id=owner_id,
            )

            attached = await PublicationService.add_segment_target(
                session, pub.id, seg.id, role="target", expected_count=900
            )
            assert attached.publication_id == pub.id
            assert attached.role == "target"

            targets = await PublicationService.list_segment_targets(session, pub.id)
            assert len(targets) == 1
            assert targets[0].external_segment_id == seg.id

            ok = await PublicationService.remove_segment_target(
                session, pub.id, seg.id
            )
            assert ok is True


@pytest.mark.asyncio
async def test_list_segment_snapshots_returns_seed_snapshot():
    async with async_session() as session:
        async with session.begin():
            owner_id = (
                await session.execute(select(TeamMember.id).limit(1))
            ).scalar_one()
            seg = await SegmentService.create(
                session,
                CFExternalSegmentCreate(
                    source="getcourse",
                    source_segment_id=f"s-{uuid.uuid4()}",
                    source_url="https://x",
                    name="X",
                    description=None,
                    population_count=10,
                    is_active=True,
                    owner_id=owner_id,
                ),
            )
            snapshots = await SegmentService.list_snapshots(session, seg.id)
            assert len(snapshots) >= 1
