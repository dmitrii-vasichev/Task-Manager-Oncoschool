import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CFGuestStory
from app.db.schemas import CFGuestStoryCreate, CFGuestStoryUpdate


class GuestStoryService:
    @staticmethod
    async def create(session: AsyncSession, payload: CFGuestStoryCreate) -> CFGuestStory:
        guest_story = CFGuestStory(**payload.model_dump())
        session.add(guest_story)
        await session.flush()
        await session.refresh(guest_story)
        return guest_story

    @staticmethod
    async def get(session: AsyncSession, guest_story_id: uuid.UUID) -> CFGuestStory | None:
        result = await session.execute(
            select(CFGuestStory).where(CFGuestStory.id == guest_story_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list(
        session: AsyncSession,
        *,
        status: str | None = None,
        owner_id: uuid.UUID | None = None,
        consent_status: str | None = None,
        bundle_id: uuid.UUID | None = None,
        publication_id: uuid.UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CFGuestStory]:
        stmt = select(CFGuestStory)
        if status:
            stmt = stmt.where(CFGuestStory.status == status)
        if owner_id:
            stmt = stmt.where(CFGuestStory.owner_id == owner_id)
        if consent_status:
            stmt = stmt.where(CFGuestStory.consent_status == consent_status)
        if bundle_id:
            stmt = stmt.where(CFGuestStory.bundle_id == bundle_id)
        if publication_id:
            stmt = stmt.where(CFGuestStory.publication_id == publication_id)
        stmt = (
            stmt.order_by(
                CFGuestStory.stage_due_at.asc().nullslast(),
                CFGuestStory.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update(
        session: AsyncSession,
        guest_story_id: uuid.UUID,
        payload: CFGuestStoryUpdate,
    ) -> CFGuestStory | None:
        guest_story = await GuestStoryService.get(session, guest_story_id)
        if guest_story is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(guest_story, field, value)
        await session.flush()
        return guest_story
