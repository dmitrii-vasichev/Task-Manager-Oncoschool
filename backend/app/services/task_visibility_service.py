import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Department, Task, TeamMember


def is_moderator_or_admin(member: TeamMember | None) -> bool:
    """Admins/moderators have company-wide visibility for tasks."""
    if not member:
        return False
    return member.role in ("admin", "moderator")


async def get_headed_department_ids(
    session: AsyncSession, member_id: uuid.UUID | None
) -> list[uuid.UUID]:
    """Return department IDs where this member is set as department head."""
    if member_id is None:
        return []

    stmt = (
        select(Department.id)
        .where(Department.head_id == member_id)
        .order_by(Department.id)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


def get_default_department_id(member: TeamMember | None) -> uuid.UUID | None:
    """For non-moderators, default scope is member.department_id."""
    if not member:
        return None
    return member.department_id


async def can_access_department(
    session: AsyncSession,
    member: TeamMember | None,
    department_id: uuid.UUID | None,
) -> bool:
    """Check access to a department; None means no explicit department filter."""
    if department_id is None:
        return True

    visible_department_ids = await resolve_visible_department_ids(session, member)
    if visible_department_ids is None:
        return True
    return department_id in visible_department_ids


async def can_access_task(
    session: AsyncSession,
    member: TeamMember | None,
    task: Task | None,
) -> bool:
    """
    Check if member can view a task by department visibility rules.

    Non-moderator users are scoped by allowed assignee departments.
    If no department scope exists, fallback is own assigned tasks only.
    """
    if task is None:
        return False

    if is_moderator_or_admin(member):
        return True

    visible_department_ids = await resolve_visible_department_ids(session, member)
    if visible_department_ids:
        assignee_department_id = (
            task.assignee.department_id if task.assignee is not None else None
        )
        return assignee_department_id in visible_department_ids

    if not member:
        return False

    return task.assignee_id == member.id


async def resolve_visible_department_ids(
    session: AsyncSession, member: TeamMember | None
) -> list[uuid.UUID] | None:
    """
    Resolve task visibility by department.

    Returns:
    - None: full company scope (admin/moderator).
    - list[UUID]: allowed department IDs for non-moderator.
      Empty list means "no department scope", so caller should fall back to own tasks.
    """
    if is_moderator_or_admin(member):
        return None
    if not member:
        return []

    visible_ids: list[uuid.UUID] = []

    default_department_id = get_default_department_id(member)
    if default_department_id:
        visible_ids.append(default_department_id)

    headed_department_ids = await get_headed_department_ids(session, member.id)
    for department_id in headed_department_ids:
        if department_id not in visible_ids:
            visible_ids.append(department_id)

    return visible_ids
