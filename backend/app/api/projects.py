import uuid
from datetime import date, datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.db.database import get_session
from app.db.models import Department, Project, ProjectDepartment, ProjectMilestone, TeamMember
from app.db.schemas import (
    PaginatedProjectsResponse,
    ProjectCommentCreate,
    ProjectCreate,
    ProjectDepartmentCreate,
    ProjectDepartmentUpdate,
    ProjectLinkedTaskCreate,
    ProjectMilestoneCreate,
    ProjectMilestoneUpdate,
    ProjectResponse,
    ProjectStatusChange,
    ProjectUpdate,
)
from app.services.idea_service import IdeaService
from app.services.notification_service import NotificationService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService

router = APIRouter(prefix="/projects", tags=["projects"])
project_service = ProjectService()
task_service = TaskService()
idea_service = IdeaService()
LINKABLE_IDEA_STATUSES = {"accepted", "in_tasks"}


async def _get_project_or_404(session: AsyncSession, project_id: uuid.UUID) -> Project:
    project = await project_service.repo.get_by_id(session, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Проект не найден")
    return project


async def _reload_and_shape(
    session: AsyncSession,
    member: TeamMember,
    project_id: uuid.UUID,
) -> ProjectResponse:
    project = await _get_project_or_404(session, project_id)
    return await project_service.shape_response(session, member, project)


async def _ensure_active_member(session: AsyncSession, member_id: uuid.UUID) -> TeamMember:
    member = await session.get(TeamMember, member_id)
    if member is None or not member.is_active:
        raise HTTPException(status_code=404, detail="Участник не найден")
    return member


async def _get_active_department_or_404(
    session: AsyncSession,
    department_id: uuid.UUID,
) -> Department:
    department = await session.get(Department, department_id)
    if department is None or not department.is_active:
        raise HTTPException(status_code=404, detail="Отдел не найден")
    return department


async def _ensure_active_department(
    session: AsyncSession,
    project_department: ProjectDepartment,
) -> Department:
    department = getattr(project_department, "department", None)
    if department is None:
        department = await session.get(Department, project_department.department_id)
    if department is None or not department.is_active:
        raise HTTPException(status_code=404, detail="Отдел не найден")
    return department


def _find_project_department_or_404(
    project: Project,
    project_department_id: uuid.UUID,
) -> ProjectDepartment:
    for item in getattr(project, "departments", []) or []:
        if item.id == project_department_id:
            return item
    raise HTTPException(status_code=404, detail="Отдел проекта не найден")


def _find_project_milestone_or_404(
    project: Project,
    project_milestone_id: uuid.UUID,
) -> ProjectMilestone:
    for item in getattr(project, "milestones", []) or []:
        if item.id == project_milestone_id:
            return item
    raise HTTPException(status_code=404, detail="Этап проекта не найден")


def _ensure_project_accepts_work_changes(project: Project) -> None:
    try:
        project_service.validate_project_accepts_work_changes(project)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _dedupe_uuids(values: list[uuid.UUID]) -> list[uuid.UUID]:
    seen = set()
    deduped = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _bot_from_request(request: Request):
    app_state = getattr(getattr(request, "app", None), "state", None)
    return getattr(app_state, "bot", None)


def _is_duplicate_project_department_error(exc: IntegrityError) -> bool:
    message = f"{exc.orig} {exc}".lower()
    return (
        "uq_project_departments_project_department" in message
        or ("project_departments" in message and "duplicate" in message)
    )


def _is_duplicate_project_task_error(exc: IntegrityError) -> bool:
    message = f"{exc.orig} {exc}".lower()
    return (
        "uq_project_tasks_task_id" in message
        or ("project_tasks" in message and "duplicate" in message)
    )


async def _handle_project_integrity_error(exc: IntegrityError, session: AsyncSession) -> None:
    await session.rollback()
    if _is_duplicate_project_department_error(exc):
        raise HTTPException(status_code=409, detail="Отдел уже добавлен к проекту") from exc
    if _is_duplicate_project_task_error(exc):
        raise HTTPException(status_code=409, detail="Задача уже связана с проектом") from exc
    raise exc


def _all_idea_task_links(idea) -> list:
    seen = set()
    links = []
    candidates = [
        *list(getattr(idea, "task_links", []) or []),
        *[
            link
            for department in (getattr(idea, "departments", []) or [])
            for link in (getattr(department, "task_links", []) or [])
        ],
    ]
    for link in candidates:
        key = getattr(link, "id", None)
        if key is None:
            key = (
                getattr(link, "task_id", None),
                getattr(link, "idea_department_id", None),
            )
        if key in seen:
            continue
        seen.add(key)
        links.append(link)
    return links


@router.get("", response_model=PaginatedProjectsResponse)
async def list_projects(
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    owner_id: uuid.UUID | None = Query(None),
    department_id: uuid.UUID | None = Query(None),
    source: Literal["idea", "direct"] | None = Query(None),
    source_idea_id: uuid.UUID | None = Query(None),
    created_from: date | None = Query(None),
    created_to: date | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PaginatedProjectsResponse:
    return await project_service.list_projects(
        session,
        member,
        status=status_filter,
        search=search,
        owner_id=owner_id,
        department_id=department_id,
        source=source,
        source_idea_id=source_idea_id,
        created_from=created_from,
        created_to=created_to,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    if data.source_idea_id is None:
        return await _create_direct_project(session, member, data)
    return await _create_project_from_idea(session, member, data)


async def _create_direct_project(
    session: AsyncSession,
    member: TeamMember,
    data: ProjectCreate,
) -> ProjectResponse:
    if not project_service.can_create_direct_project(member):
        raise HTTPException(status_code=403, detail="Недостаточно прав для создания проекта")

    await _ensure_active_member(session, data.owner_id)
    department_ids = _dedupe_uuids(data.department_ids)
    for department_id in department_ids:
        await _get_active_department_or_404(session, department_id)

    try:
        project = await project_service.repo.create(
            session,
            title=data.title,
            description=data.description,
            owner_id=data.owner_id,
            source_idea_id=None,
        )
        await project_service.repo.add_event(
            session,
            project_id=project.id,
            actor_id=member.id,
            event_type="project_created",
            payload={"title": data.title, "source": "direct"},
        )
        for department_id in department_ids:
            await project_service.repo.add_department(
                session,
                project_id=project.id,
                department_id=department_id,
                owner_id=data.owner_id,
                created_by_id=member.id,
            )
            await project_service.repo.add_event(
                session,
                project_id=project.id,
                actor_id=member.id,
                event_type="department_added",
                payload={
                    "department_id": str(department_id),
                    "owner_id": str(data.owner_id),
                },
            )
    except IntegrityError as exc:
        await _handle_project_integrity_error(exc, session)

    await session.commit()
    return await _reload_and_shape(session, member, project.id)


async def _create_project_from_idea(
    session: AsyncSession,
    member: TeamMember,
    data: ProjectCreate,
) -> ProjectResponse:
    await _ensure_active_member(session, data.owner_id)
    idea = await idea_service.repo.get_by_id(session, data.source_idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Идея не найдена")
    if idea.status not in LINKABLE_IDEA_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Проект можно создать только из принятой идеи или идеи в задачах",
        )
    if idea.project_id is not None:
        linked_project = getattr(idea, "project", None)
        if linked_project is None or getattr(linked_project, "deleted_at", None) is None:
            raise HTTPException(status_code=409, detail="По этой идее уже создан проект")
    if not (
        project_service.can_create_direct_project(member)
        or idea_service.can_manage_idea(member, idea)
    ):
        raise HTTPException(status_code=403, detail="Недостаточно прав для создания проекта")

    idea_departments = list(getattr(idea, "departments", []) or [])
    idea_department_by_id = {item.id: item for item in idea_departments}
    idea_department_by_department_id = {
        item.department_id: item for item in idea_departments
    }
    department_ids = _dedupe_uuids(
        data.department_ids
        or [item.department_id for item in idea_departments]
    )
    for department_id in department_ids:
        await _get_active_department_or_404(session, department_id)

    department_to_project_department_id: dict[uuid.UUID, uuid.UUID] = {}
    try:
        project = await project_service.repo.create(
            session,
            title=data.title,
            description=data.description,
            owner_id=data.owner_id,
            source_idea_id=idea.id,
        )
        await project_service.repo.add_event(
            session,
            project_id=project.id,
            actor_id=member.id,
            event_type="project_created",
            payload={
                "title": data.title,
                "source": "idea",
                "source_idea_id": str(idea.id),
            },
        )
        for department_id in department_ids:
            idea_department = idea_department_by_department_id.get(department_id)
            department_owner_id = (
                idea_department.owner_id if idea_department is not None else data.owner_id
            )
            project_department = await project_service.repo.add_department(
                session,
                project_id=project.id,
                department_id=department_id,
                owner_id=department_owner_id,
                created_by_id=member.id,
            )
            department_to_project_department_id[department_id] = project_department.id
            await project_service.repo.add_event(
                session,
                project_id=project.id,
                actor_id=member.id,
                event_type="department_added",
                payload={
                    "department_id": str(department_id),
                    "owner_id": str(department_owner_id),
                },
            )

        await idea_service.repo.update(session, idea, project_id=project.id)
        for link in _all_idea_task_links(idea):
            project_department_id = None
            idea_department_id = getattr(link, "idea_department_id", None)
            if idea_department_id is not None:
                idea_department = idea_department_by_id.get(idea_department_id)
                if idea_department is not None:
                    project_department_id = department_to_project_department_id.get(
                        idea_department.department_id
                    )
            await project_service.repo.add_task_link(
                session,
                project_id=project.id,
                project_department_id=project_department_id,
                task_id=link.task_id,
                created_by_id=getattr(link, "created_by_id", None) or member.id,
            )

        await idea_service.repo.add_event(
            session,
            idea_id=idea.id,
            actor_id=member.id,
            event_type="project_created",
            payload={"project_id": str(project.id), "title": data.title},
        )
        await idea_service.repo.add_event(
            session,
            idea_id=idea.id,
            actor_id=member.id,
            event_type="project_linked",
            payload={"project_id": str(project.id)},
        )
    except IntegrityError as exc:
        await _handle_project_integrity_error(exc, session)

    await session.commit()
    return await _reload_and_shape(session, member, project.id)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    project = await _get_project_or_404(session, project_id)
    return await project_service.shape_response(session, member, project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    project = await _get_project_or_404(session, project_id)
    if not project_service.can_manage_project(member, project):
        raise HTTPException(status_code=403, detail="Недостаточно прав для изменения проекта")

    fields = {
        key: value
        for key, value in data.model_dump(exclude_unset=True).items()
        if value is not None
    }
    if "owner_id" in fields:
        await _ensure_active_member(session, fields["owner_id"])
    if fields:
        await project_service.repo.update(session, project, **fields)
    await project_service.repo.add_event(
        session,
        project_id=project.id,
        actor_id=member.id,
        event_type="project_updated",
        payload={"fields": list(fields)},
    )
    await session.commit()
    return await _reload_and_shape(session, member, project.id)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    project = await _get_project_or_404(session, project_id)
    try:
        project_service.validate_delete_project(member, project)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await project_service.repo.add_event(
        session,
        project_id=project.id,
        actor_id=member.id,
        event_type="project_deleted",
        payload={"status": project.status},
    )
    await project_service.repo.soft_delete(
        session,
        project,
        deleted_by_id=member.id,
        deleted_at=deleted_at,
    )
    source_idea = getattr(project, "source_idea", None)
    if source_idea is not None and getattr(source_idea, "project_id", None) == project.id:
        await idea_service.repo.update(session, source_idea, project_id=None)
    await session.commit()


@router.post("/{project_id}/status", response_model=ProjectResponse)
async def change_project_status(
    project_id: uuid.UUID,
    data: ProjectStatusChange,
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    project = await _get_project_or_404(session, project_id)
    try:
        await project_service.record_status_change(
            session,
            project=project,
            member=member,
            status=data.status,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await session.commit()
    return await _reload_and_shape(session, member, project.id)


@router.post("/{project_id}/departments", response_model=ProjectResponse)
async def add_project_department(
    project_id: uuid.UUID,
    data: ProjectDepartmentCreate,
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    project = await _get_project_or_404(session, project_id)
    _ensure_project_accepts_work_changes(project)
    department = await _get_active_department_or_404(session, data.department_id)
    await _ensure_active_member(session, data.owner_id)
    if not project_service.can_add_department(member, project, department):
        raise HTTPException(status_code=403, detail="Недостаточно прав для добавления отдела")

    try:
        await project_service.repo.add_department(
            session,
            project_id=project.id,
            department_id=data.department_id,
            owner_id=data.owner_id,
            created_by_id=member.id,
        )
    except IntegrityError as exc:
        await _handle_project_integrity_error(exc, session)

    await project_service.repo.add_event(
        session,
        project_id=project.id,
        actor_id=member.id,
        event_type="department_added",
        payload={
            "department_id": str(data.department_id),
            "owner_id": str(data.owner_id),
        },
    )
    await session.commit()
    return await _reload_and_shape(session, member, project.id)


@router.patch(
    "/{project_id}/departments/{project_department_id}",
    response_model=ProjectResponse,
)
async def update_project_department(
    project_id: uuid.UUID,
    project_department_id: uuid.UUID,
    data: ProjectDepartmentUpdate,
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    project = await _get_project_or_404(session, project_id)
    project_department = _find_project_department_or_404(project, project_department_id)
    await _ensure_active_department(session, project_department)
    if not project_service.can_manage_project_department(member, project, project_department):
        raise HTTPException(status_code=403, detail="Недостаточно прав для изменения отдела")
    _ensure_project_accepts_work_changes(project)

    updates = data.model_dump(exclude_unset=True)
    if updates.get("owner_id") is not None:
        await _ensure_active_member(session, updates["owner_id"])
    if updates.get("status") == "ready" and not project_service.can_mark_department_ready(
        project_department
    ):
        raise HTTPException(
            status_code=400,
            detail="Отдел нельзя отметить готовым: не все связанные задачи закрыты",
        )
    for field in ("owner_id", "status", "note"):
        if field in updates:
            value = updates[field]
            if field != "note" and value is None:
                continue
            setattr(project_department, field, value)

    await session.flush()
    await project_service.repo.add_event(
        session,
        project_id=project.id,
        actor_id=member.id,
        event_type="department_updated",
        payload={
            "project_department_id": str(project_department.id),
            "fields": list(updates),
        },
    )
    await session.commit()
    return await _reload_and_shape(session, member, project.id)


@router.post("/{project_id}/milestones", response_model=ProjectResponse)
async def add_project_milestone(
    project_id: uuid.UUID,
    data: ProjectMilestoneCreate,
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    project = await _get_project_or_404(session, project_id)
    if not project_service.can_manage_project(member, project):
        raise HTTPException(status_code=403, detail="Недостаточно прав для добавления этапа")
    _ensure_project_accepts_work_changes(project)

    milestone = await project_service.repo.add_milestone(
        session,
        project_id=project.id,
        title=data.title,
        due_date=data.due_date,
        sort_order=len(getattr(project, "milestones", []) or []),
    )
    await project_service.repo.add_event(
        session,
        project_id=project.id,
        actor_id=member.id,
        event_type="milestone_added",
        payload={"milestone_id": str(milestone.id), "title": data.title},
    )
    await session.commit()
    return await _reload_and_shape(session, member, project.id)


@router.patch(
    "/{project_id}/milestones/{project_milestone_id}",
    response_model=ProjectResponse,
)
async def update_project_milestone(
    project_id: uuid.UUID,
    project_milestone_id: uuid.UUID,
    data: ProjectMilestoneUpdate,
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    project = await _get_project_or_404(session, project_id)
    milestone = _find_project_milestone_or_404(project, project_milestone_id)
    if not project_service.can_manage_project(member, project):
        raise HTTPException(status_code=403, detail="Недостаточно прав для изменения этапа")
    _ensure_project_accepts_work_changes(project)

    updates = data.model_dump(exclude_unset=True)
    fields = {}
    for key, value in updates.items():
        if key in {"title", "status", "sort_order"} and value is None:
            continue
        fields[key] = value
    if fields:
        await project_service.repo.update_milestone(session, milestone, **fields)
    await project_service.repo.add_event(
        session,
        project_id=project.id,
        actor_id=member.id,
        event_type="milestone_updated",
        payload={"milestone_id": str(milestone.id), "fields": list(fields)},
    )
    await session.commit()
    return await _reload_and_shape(session, member, project.id)


@router.post("/{project_id}/comments", response_model=ProjectResponse)
async def add_project_comment(
    project_id: uuid.UUID,
    data: ProjectCommentCreate,
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    if not getattr(member, "is_active", True):
        raise HTTPException(status_code=403, detail="Пользователь неактивен")
    project = await _get_project_or_404(session, project_id)
    comment = await project_service.repo.add_comment(
        session,
        project_id=project.id,
        author_id=member.id,
        body=data.body,
    )
    await project_service.repo.add_event(
        session,
        project_id=project.id,
        actor_id=member.id,
        event_type="comment_added",
        payload={"comment_id": str(comment.id)},
    )
    await session.commit()
    return await _reload_and_shape(session, member, project.id)


@router.post("/{project_id}/tasks", response_model=ProjectResponse)
async def create_project_task(
    project_id: uuid.UUID,
    data: ProjectLinkedTaskCreate,
    request: Request,
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    project = await _get_project_or_404(session, project_id)
    if not project_service.can_manage_project(member, project):
        raise HTTPException(status_code=403, detail="Недостаточно прав для создания задачи")
    _ensure_project_accepts_work_changes(project)

    return await _create_linked_task(
        request,
        session,
        member,
        project,
        data,
        project_department_id=None,
    )


@router.post(
    "/{project_id}/departments/{project_department_id}/tasks",
    response_model=ProjectResponse,
)
async def create_project_department_task(
    project_id: uuid.UUID,
    project_department_id: uuid.UUID,
    data: ProjectLinkedTaskCreate,
    request: Request,
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    project = await _get_project_or_404(session, project_id)
    project_department = _find_project_department_or_404(project, project_department_id)
    await _ensure_active_department(session, project_department)
    if not project_service.can_manage_project_department(member, project, project_department):
        raise HTTPException(status_code=403, detail="Недостаточно прав для создания задачи")
    _ensure_project_accepts_work_changes(project)

    return await _create_linked_task(
        request,
        session,
        member,
        project,
        data,
        project_department_id=project_department.id,
    )


async def _create_linked_task(
    request: Request,
    session: AsyncSession,
    member: TeamMember,
    project: Project,
    data: ProjectLinkedTaskCreate,
    project_department_id: uuid.UUID | None,
) -> ProjectResponse:
    try:
        task = await task_service.create_task(
            session=session,
            title=data.title,
            creator=member,
            assignee_id=data.assignee_id,
            description=data.description,
            checklist=[],
            priority=data.priority,
            deadline=data.deadline,
            source="web",
            label_ids=data.label_ids,
        )
        await project_service.repo.add_task_link(
            session,
            project_id=project.id,
            project_department_id=project_department_id,
            task_id=task.id,
            created_by_id=member.id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrityError as exc:
        await _handle_project_integrity_error(exc, session)

    await project_service.repo.add_event(
        session,
        project_id=project.id,
        actor_id=member.id,
        event_type="task_linked",
        payload={
            "task_id": str(task.id),
            "project_department_id": str(project_department_id)
            if project_department_id is not None
            else None,
        },
    )

    bot = _bot_from_request(request)
    if bot is not None:
        await NotificationService(bot).notify_task_created(session, task, member)

    await session.commit()
    return await _reload_and_shape(session, member, project.id)
