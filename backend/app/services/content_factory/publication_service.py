from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CFPublication, CFPublicationVariant, CFPublicationVersion
from app.db.schemas import (
    CFPublicationCreate,
    CFPublicationUpdate,
    CFPublicationVariantUpsert,
)

if TYPE_CHECKING:
    from app.db.models import CFPublicationSegmentTarget


class PublicationWorkflowTransitionError(ValueError):
    """Raised when a publication status move breaks the editorial workflow."""


CF_PUBLICATION_STATUS_LABELS = {
    "draft": "Черновик",
    "needs_copy": "Нужен текст",
    "needs_design": "Нужен дизайн",
    "factcheck": "Фактчек",
    "doctor_review": "Проверка врача",
    "approved": "Одобрено",
    "scheduled": "Запланировано",
    "published": "Опубликовано",
    "failed": "Ошибка",
    "cancelled": "Отменено",
}

CF_PUBLICATION_STATUS_APPROVAL_EVENTS = {
    "draft": "drafted",
    "needs_copy": "reviewed",
    "needs_design": "reviewed",
    "factcheck": "reviewed",
    "doctor_review": "reviewed",
    "approved": "doctor_approved",
    "scheduled": "scheduled",
    "published": "published",
    "failed": "rolled_back",
    "cancelled": "rolled_back",
}

CF_PUBLICATION_ALLOWED_STATUS_TRANSITIONS = {
    "draft": {"needs_copy", "cancelled"},
    "needs_copy": {"needs_design", "factcheck", "cancelled"},
    "needs_design": {"factcheck", "cancelled"},
    "factcheck": {"doctor_review", "needs_copy", "cancelled"},
    "doctor_review": {"approved", "needs_copy", "cancelled"},
    "approved": {"scheduled", "doctor_review", "cancelled", "published"},
    "scheduled": {"approved", "cancelled", "published"},
    "failed": {"needs_copy", "cancelled"},
    "cancelled": {"draft"},
    "published": set(),
}


def _status_label(status: str | None) -> str:
    if not status:
        return "Статус не задан"
    return CF_PUBLICATION_STATUS_LABELS.get(status, status)


def _approval_event_for_status(status: str | None) -> str:
    if not status:
        return "reviewed"
    return CF_PUBLICATION_STATUS_APPROVAL_EVENTS.get(status, "reviewed")


def _validate_status_transition(
    old_status: str | None,
    new_status: str | None,
    changes: dict,
    current_scheduled_at,
) -> None:
    if not new_status or new_status == old_status:
        return

    allowed_targets = CF_PUBLICATION_ALLOWED_STATUS_TRANSITIONS.get(
        old_status or "",
        set(),
    )
    if new_status not in allowed_targets:
        raise PublicationWorkflowTransitionError(
            f"Недопустимый переход статуса: "
            f"{_status_label(old_status)} -> {_status_label(new_status)}"
        )

    if old_status == "approved" and new_status == "scheduled":
        scheduled_at = (
            changes["scheduled_at"]
            if "scheduled_at" in changes
            else current_scheduled_at
        )
        if scheduled_at is None:
            raise PublicationWorkflowTransitionError(
                "Укажите плановую дату перед переводом в календарь"
            )


class PublicationService:
    @staticmethod
    async def create(
        session: AsyncSession,
        payload: CFPublicationCreate,
        *,
        editor_id: uuid.UUID,
    ) -> CFPublication:
        pub = CFPublication(
            bundle_id=payload.bundle_id,
            platform_id=payload.platform_id,
            format_id=payload.format_id,
            rubric_id=payload.rubric_id,
            nosology_id=payload.nosology_id,
            title=payload.title,
            body_text=payload.body_text,
            media_refs=payload.media_refs,
            scheduled_at=payload.scheduled_at,
            responsible_id=payload.responsible_id,
            status=payload.status,
            utm=payload.utm,
            version_number=1,
        )
        session.add(pub)
        await session.flush()

        version = CFPublicationVersion(
            publication_id=pub.id,
            version_number=1,
            body_text=pub.body_text,
            edited_by_id=editor_id,
            approval_event="drafted",
            source_materials_refs=[],
        )
        session.add(version)
        await session.flush()
        await session.refresh(pub)
        return pub

    @staticmethod
    async def get(session: AsyncSession, pub_id: uuid.UUID) -> CFPublication | None:
        result = await session.execute(select(CFPublication).where(CFPublication.id == pub_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_bundle(session: AsyncSession, bundle_id: uuid.UUID) -> list[CFPublication]:
        result = await session.execute(
            select(CFPublication).where(CFPublication.bundle_id == bundle_id).order_by(CFPublication.scheduled_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list(
        session: AsyncSession,
        *,
        bundle_id: uuid.UUID | None = None,
        status: str | None = None,
        platform_id: uuid.UUID | None = None,
        format_id: uuid.UUID | None = None,
        responsible_id: uuid.UUID | None = None,
        scheduled_from: datetime | None = None,
        scheduled_to: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CFPublication]:
        stmt = select(CFPublication)
        if bundle_id:
            stmt = stmt.where(CFPublication.bundle_id == bundle_id)
        if status:
            stmt = stmt.where(CFPublication.status == status)
        if platform_id:
            stmt = stmt.where(CFPublication.platform_id == platform_id)
        if format_id:
            stmt = stmt.where(CFPublication.format_id == format_id)
        if responsible_id:
            stmt = stmt.where(CFPublication.responsible_id == responsible_id)
        if scheduled_from:
            stmt = stmt.where(CFPublication.scheduled_at >= scheduled_from)
        if scheduled_to:
            stmt = stmt.where(CFPublication.scheduled_at <= scheduled_to)
        stmt = stmt.order_by(
            CFPublication.scheduled_at.asc().nullslast(),
            CFPublication.created_at.desc(),
        )
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update(
        session: AsyncSession,
        pub_id: uuid.UUID,
        payload: CFPublicationUpdate,
        *,
        editor_id: uuid.UUID,
        approval_event: str | None = None,
    ) -> CFPublication | None:
        pub = await PublicationService.get(session, pub_id)
        if pub is None:
            return None

        changes = payload.model_dump(exclude_unset=True)
        old_status = pub.status
        new_status = changes.get("status")
        _validate_status_transition(
            old_status,
            new_status,
            changes,
            getattr(pub, "scheduled_at", None),
        )
        body_changed = "body_text" in changes and changes["body_text"] != pub.body_text
        status_changed = "status" in changes and changes["status"] != old_status

        for field, value in changes.items():
            setattr(pub, field, value)

        if body_changed or status_changed:
            pub.version_number = (pub.version_number or 1) + 1
            status_note = (
                f"Статус: {_status_label(old_status)} -> {_status_label(pub.status)}"
                if status_changed
                else None
            )
            version = CFPublicationVersion(
                publication_id=pub.id,
                version_number=pub.version_number,
                body_text=pub.body_text,
                edited_by_id=editor_id,
                approval_event=approval_event or _approval_event_for_status(pub.status),
                source_materials_refs=[],
                notes=status_note,
            )
            session.add(version)

        if "status" in changes and changes["status"] == "published" and pub.actual_published_at is None:
            pub.actual_published_at = datetime.now(timezone.utc)

        await session.flush()
        return pub

    @staticmethod
    async def list_versions(
        session: AsyncSession, publication_id: uuid.UUID
    ) -> list[CFPublicationVersion]:
        result = await session.execute(
            select(CFPublicationVersion)
            .where(CFPublicationVersion.publication_id == publication_id)
            .order_by(CFPublicationVersion.version_number)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_variants(
        session: AsyncSession, publication_id: uuid.UUID
    ) -> list[CFPublicationVariant]:
        result = await session.execute(
            select(CFPublicationVariant)
            .where(CFPublicationVariant.publication_id == publication_id)
            .order_by(CFPublicationVariant.channel)
        )
        return list(result.scalars().all())

    @staticmethod
    async def upsert_variant(
        session: AsyncSession,
        publication_id: uuid.UUID,
        channel: str,
        payload: CFPublicationVariantUpsert,
        *,
        editor_id: uuid.UUID,
    ) -> CFPublicationVariant | None:
        publication = await PublicationService.get(session, publication_id)
        if publication is None:
            return None

        result = await session.execute(
            select(CFPublicationVariant).where(
                CFPublicationVariant.publication_id == publication_id,
                CFPublicationVariant.channel == channel,
            )
        )
        variant = result.scalar_one_or_none()
        source_version_number = publication.version_number or 1
        if variant is None:
            variant = CFPublicationVariant(
                publication_id=publication_id,
                channel=channel,
                title=payload.title,
                body_text=payload.body_text,
                notes=payload.notes,
                source_version_number=source_version_number,
                updated_by_id=editor_id,
            )
            session.add(variant)
        else:
            variant.title = payload.title
            variant.body_text = payload.body_text
            variant.notes = payload.notes
            variant.source_version_number = source_version_number
            variant.updated_by_id = editor_id
            variant.updated_at = datetime.now(timezone.utc)

        await session.flush()
        return variant

    @staticmethod
    async def add_segment_target(
        session: AsyncSession,
        publication_id: uuid.UUID,
        external_segment_id: uuid.UUID,
        *,
        role: str,
        expected_count: int | None = None,
    ) -> "CFPublicationSegmentTarget":
        from app.db.models import CFPublicationSegmentTarget
        target = CFPublicationSegmentTarget(
            publication_id=publication_id,
            external_segment_id=external_segment_id,
            role=role,
            expected_count=expected_count,
        )
        session.add(target)
        await session.flush()
        await session.refresh(target)
        return target

    @staticmethod
    async def remove_segment_target(
        session: AsyncSession,
        publication_id: uuid.UUID,
        external_segment_id: uuid.UUID,
    ) -> bool:
        from app.db.models import CFPublicationSegmentTarget
        result = await session.execute(
            select(CFPublicationSegmentTarget).where(
                CFPublicationSegmentTarget.publication_id == publication_id,
                CFPublicationSegmentTarget.external_segment_id == external_segment_id,
            )
        )
        target = result.scalar_one_or_none()
        if target is None:
            return False
        await session.delete(target)
        await session.flush()
        return True

    @staticmethod
    async def list_segment_targets(
        session: AsyncSession, publication_id: uuid.UUID
    ) -> list["CFPublicationSegmentTarget"]:
        from app.db.models import CFPublicationSegmentTarget
        result = await session.execute(
            select(CFPublicationSegmentTarget).where(
                CFPublicationSegmentTarget.publication_id == publication_id
            )
        )
        return list(result.scalars().all())
