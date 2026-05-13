import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api import projects as projects_api
from app.db.models import Department, TeamMember
from app.db.schemas import (
    ProjectCreate,
    ProjectDepartmentUpdate,
    ProjectLinkedTaskCreate,
    ProjectMilestoneCreate,
    ProjectMilestoneUpdate,
    ProjectStatusChange,
)


def active_member(member_id: uuid.UUID | None = None, *, role: str = "member"):
    return SimpleNamespace(id=member_id or uuid.uuid4(), is_active=True, role=role)


def active_department(department_id: uuid.UUID | None = None):
    return SimpleNamespace(id=department_id or uuid.uuid4(), is_active=True)


def project_create_data(**overrides):
    base = {
        "title": "Patient onboarding redesign",
        "description": "Coordinate launch work",
        "owner_id": uuid.uuid4(),
        "department_ids": [],
    }
    base.update(overrides)
    return ProjectCreate(**base)


@pytest.mark.asyncio
async def test_create_direct_project_rejects_normal_members(monkeypatch):
    member = active_member(role="member")
    data = project_create_data(owner_id=member.id)
    session = AsyncMock()

    async def get_model(model, item_id):
        if model is TeamMember and item_id == member.id:
            return member
        return None

    session.get.side_effect = get_model
    monkeypatch.setattr(projects_api.project_service.repo, "create", AsyncMock())

    with pytest.raises(HTTPException) as exc_info:
        await projects_api.create_project(data=data, member=member, session=session)

    assert exc_info.value.status_code == 403
    projects_api.project_service.repo.create.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_direct_project_by_admin_commits_and_returns_shaped_response(monkeypatch):
    admin = active_member(role="admin")
    owner_id = uuid.uuid4()
    project_id = uuid.uuid4()
    data = project_create_data(owner_id=owner_id)
    session = AsyncMock()
    created_project = SimpleNamespace(id=project_id)
    shaped_response = SimpleNamespace(id=project_id)

    async def get_model(model, item_id):
        if model is TeamMember and item_id == owner_id:
            return active_member(owner_id)
        return None

    session.get.side_effect = get_model
    create = AsyncMock(return_value=created_project)
    add_event = AsyncMock()
    monkeypatch.setattr(projects_api.project_service.repo, "create", create)
    monkeypatch.setattr(projects_api.project_service.repo, "add_event", add_event)
    monkeypatch.setattr(
        projects_api.project_service.repo,
        "get_by_id",
        AsyncMock(return_value=created_project),
    )
    monkeypatch.setattr(
        projects_api.project_service,
        "shape_response",
        AsyncMock(return_value=shaped_response),
    )

    response = await projects_api.create_project(data=data, member=admin, session=session)

    assert response.id == project_id
    create.assert_awaited_once_with(
        session,
        title=data.title,
        description=data.description,
        owner_id=owner_id,
        source_idea_id=None,
    )
    assert add_event.await_args.kwargs["event_type"] == "project_created"
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_project_from_accepted_idea_copies_departments_and_task_links(
    monkeypatch,
):
    admin = active_member(role="admin")
    owner_id = uuid.uuid4()
    project_id = uuid.uuid4()
    source_idea_id = uuid.uuid4()
    department_id = uuid.uuid4()
    second_department_id = uuid.uuid4()
    idea_department_id = uuid.uuid4()
    second_idea_department_id = uuid.uuid4()
    project_department_id = uuid.uuid4()
    second_project_department_id = uuid.uuid4()
    direct_task_id = uuid.uuid4()
    department_task_id = uuid.uuid4()
    idea_department_owner_id = uuid.uuid4()
    second_idea_department_owner_id = uuid.uuid4()
    data = project_create_data(owner_id=owner_id, source_idea_id=source_idea_id)
    session = AsyncMock()
    project = SimpleNamespace(id=project_id)
    shaped_response = SimpleNamespace(id=project_id)
    idea_departments = [
        SimpleNamespace(
            id=idea_department_id,
            department_id=department_id,
            owner_id=idea_department_owner_id,
            department=active_department(department_id),
        ),
        SimpleNamespace(
            id=second_idea_department_id,
            department_id=second_department_id,
            owner_id=second_idea_department_owner_id,
            department=active_department(second_department_id),
        ),
    ]
    idea = SimpleNamespace(
        id=source_idea_id,
        title="Accepted idea",
        status="accepted",
        project_id=None,
        review_owner_id=uuid.uuid4(),
        departments=idea_departments,
        task_links=[
            SimpleNamespace(
                task_id=direct_task_id,
                idea_department_id=None,
                created_by_id=uuid.uuid4(),
            ),
            SimpleNamespace(
                task_id=department_task_id,
                idea_department_id=idea_department_id,
                created_by_id=uuid.uuid4(),
            ),
        ],
    )

    async def get_model(model, item_id):
        if model is TeamMember and item_id == owner_id:
            return active_member(owner_id)
        if model is Department and item_id in {department_id, second_department_id}:
            return active_department(item_id)
        return None

    session.get.side_effect = get_model
    add_department = AsyncMock(
        side_effect=[
            SimpleNamespace(id=project_department_id, department_id=department_id),
            SimpleNamespace(
                id=second_project_department_id,
                department_id=second_department_id,
            ),
        ]
    )
    add_task_link = AsyncMock()
    idea_add_event = AsyncMock()
    monkeypatch.setattr(
        projects_api.idea_service.repo,
        "get_by_id",
        AsyncMock(return_value=idea),
    )
    monkeypatch.setattr(projects_api.idea_service.repo, "add_event", idea_add_event)
    monkeypatch.setattr(
        projects_api.project_service.repo,
        "create",
        AsyncMock(return_value=project),
    )
    monkeypatch.setattr(
        projects_api.project_service.repo,
        "add_department",
        add_department,
    )
    monkeypatch.setattr(
        projects_api.project_service.repo,
        "add_task_link",
        add_task_link,
    )
    monkeypatch.setattr(projects_api.project_service.repo, "add_event", AsyncMock())
    monkeypatch.setattr(
        projects_api.project_service.repo,
        "get_by_id",
        AsyncMock(return_value=project),
    )
    monkeypatch.setattr(
        projects_api.project_service,
        "shape_response",
        AsyncMock(return_value=shaped_response),
    )

    response = await projects_api.create_project(data=data, member=admin, session=session)

    assert response.id == project_id
    assert idea.project_id == project_id
    assert add_department.await_count == 2
    assert add_department.await_args_list[0].kwargs["owner_id"] == idea_department_owner_id
    assert (
        add_department.await_args_list[1].kwargs["owner_id"]
        == second_idea_department_owner_id
    )
    assert add_task_link.await_count == 2
    copied_links = {
        call.kwargs["task_id"]: call.kwargs["project_department_id"]
        for call in add_task_link.await_args_list
    }
    assert copied_links[direct_task_id] is None
    assert copied_links[department_task_id] == project_department_id
    assert [
        call.kwargs["event_type"] for call in idea_add_event.await_args_list
    ] == ["project_created", "project_linked"]
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_project_from_idea_rejects_non_review_owner_even_when_selected_owner(
    monkeypatch,
):
    member = active_member(role="member")
    source_idea_id = uuid.uuid4()
    data = project_create_data(owner_id=member.id, source_idea_id=source_idea_id)
    idea = SimpleNamespace(
        id=source_idea_id,
        status="accepted",
        project_id=None,
        review_owner_id=uuid.uuid4(),
        departments=[],
        task_links=[],
    )
    session = AsyncMock()

    async def get_model(model, item_id):
        if model is TeamMember and item_id == member.id:
            return member
        return None

    session.get.side_effect = get_model
    create = AsyncMock(return_value=SimpleNamespace(id=uuid.uuid4()))
    monkeypatch.setattr(
        projects_api.idea_service.repo,
        "get_by_id",
        AsyncMock(return_value=idea),
    )
    monkeypatch.setattr(projects_api.project_service.repo, "create", create)

    with pytest.raises(HTTPException) as exc_info:
        await projects_api.create_project(data=data, member=member, session=session)

    assert exc_info.value.status_code == 403
    create.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_project_clears_source_idea_project_link(monkeypatch):
    admin = active_member(role="admin")
    project_id = uuid.uuid4()
    source_idea = SimpleNamespace(id=uuid.uuid4(), project_id=project_id)
    project = SimpleNamespace(
        id=project_id,
        owner_id=uuid.uuid4(),
        status="planned",
        task_links=[],
        departments=[],
        source_idea=source_idea,
    )
    session = AsyncMock()
    soft_delete = AsyncMock()
    idea_update = AsyncMock()
    monkeypatch.setattr(
        projects_api.project_service.repo,
        "get_by_id",
        AsyncMock(return_value=project),
    )
    monkeypatch.setattr(projects_api.project_service.repo, "add_event", AsyncMock())
    monkeypatch.setattr(projects_api.project_service.repo, "soft_delete", soft_delete)
    monkeypatch.setattr(projects_api.idea_service.repo, "update", idea_update)

    await projects_api.delete_project(
        project_id=project.id,
        member=admin,
        session=session,
    )

    idea_update.assert_awaited_once_with(session, source_idea, project_id=None)
    soft_delete.assert_awaited_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_change_project_status_completed_rejects_when_gate_fails(monkeypatch):
    owner = active_member(role="admin")
    project = SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner.id,
        status="in_progress",
        task_links=[],
        departments=[],
    )
    session = AsyncMock()
    update = AsyncMock()
    monkeypatch.setattr(
        projects_api.project_service.repo,
        "get_by_id",
        AsyncMock(return_value=project),
    )
    monkeypatch.setattr(projects_api.project_service.repo, "update", update)

    with pytest.raises(HTTPException) as exc_info:
        await projects_api.change_project_status(
            project_id=project.id,
            data=ProjectStatusChange(status="completed"),
            member=owner,
            session=session,
        )

    assert exc_info.value.status_code == 400
    update.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_project_milestone_rejects_completed_project(monkeypatch):
    owner = active_member(role="member")
    project = SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner.id,
        status="completed",
        task_links=[],
        departments=[],
    )
    add_milestone = AsyncMock()
    session = AsyncMock()
    monkeypatch.setattr(
        projects_api.project_service.repo,
        "get_by_id",
        AsyncMock(return_value=project),
    )
    monkeypatch.setattr(projects_api.project_service.repo, "add_milestone", add_milestone)

    with pytest.raises(HTTPException) as exc_info:
        await projects_api.add_project_milestone(
            project_id=project.id,
            data=ProjectMilestoneCreate(title="Launch"),
            member=owner,
            session=session,
        )

    assert exc_info.value.status_code == 400
    add_milestone.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_project_milestone_rejects_cancelled_project(monkeypatch):
    owner = active_member(role="member")
    milestone = SimpleNamespace(id=uuid.uuid4(), status="planned")
    project = SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner.id,
        status="cancelled",
        milestones=[milestone],
        task_links=[],
        departments=[],
    )
    update_milestone = AsyncMock()
    session = AsyncMock()
    monkeypatch.setattr(
        projects_api.project_service.repo,
        "get_by_id",
        AsyncMock(return_value=project),
    )
    monkeypatch.setattr(
        projects_api.project_service.repo,
        "update_milestone",
        update_milestone,
    )

    with pytest.raises(HTTPException) as exc_info:
        await projects_api.update_project_milestone(
            project_id=project.id,
            project_milestone_id=milestone.id,
            data=ProjectMilestoneUpdate(status="done"),
            member=owner,
            session=session,
        )

    assert exc_info.value.status_code == 400
    update_milestone.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_project_department_rejects_completed_project(monkeypatch):
    owner = active_member(role="member")
    project_department = SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner.id,
        department=active_department(),
        task_links=[],
    )
    project = SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner.id,
        status="completed",
        task_links=[],
        departments=[project_department],
    )
    session = AsyncMock()
    monkeypatch.setattr(
        projects_api.project_service.repo,
        "get_by_id",
        AsyncMock(return_value=project),
    )

    with pytest.raises(HTTPException) as exc_info:
        await projects_api.update_project_department(
            project_id=project.id,
            project_department_id=project_department.id,
            data=ProjectDepartmentUpdate(status="ready"),
            member=owner,
            session=session,
        )

    assert exc_info.value.status_code == 400
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_project_task_rejects_completed_project(monkeypatch):
    owner = active_member(role="member")
    project = SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner.id,
        status="completed",
        task_links=[],
        departments=[],
    )
    create_task = AsyncMock()
    session = AsyncMock()
    monkeypatch.setattr(
        projects_api.project_service.repo,
        "get_by_id",
        AsyncMock(return_value=project),
    )
    monkeypatch.setattr(projects_api.task_service, "create_task", create_task)

    with pytest.raises(HTTPException) as exc_info:
        await projects_api.create_project_task(
            project_id=project.id,
            data=ProjectLinkedTaskCreate(title="Prepare launch"),
            request=SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(bot=None))),
            member=owner,
            session=session,
        )

    assert exc_info.value.status_code == 400
    create_task.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_project_rejects_linked_tasks_without_soft_delete_or_commit(
    monkeypatch,
):
    admin = active_member(role="admin")
    project = SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        status="planned",
        task_links=[SimpleNamespace(id=uuid.uuid4())],
        departments=[],
    )
    session = AsyncMock()
    add_event = AsyncMock()
    soft_delete = AsyncMock()
    monkeypatch.setattr(
        projects_api.project_service.repo,
        "get_by_id",
        AsyncMock(return_value=project),
    )
    monkeypatch.setattr(projects_api.project_service.repo, "add_event", add_event)
    monkeypatch.setattr(projects_api.project_service.repo, "soft_delete", soft_delete)

    with pytest.raises(HTTPException) as exc_info:
        await projects_api.delete_project(
            project_id=project.id,
            member=admin,
            session=session,
        )

    assert exc_info.value.status_code == 400
    add_event.assert_not_awaited()
    soft_delete.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_project_returns_404_when_project_is_missing(monkeypatch):
    monkeypatch.setattr(
        projects_api.project_service.repo,
        "get_by_id",
        AsyncMock(return_value=None),
    )

    with pytest.raises(HTTPException) as exc_info:
        await projects_api.get_project(
            project_id=uuid.uuid4(),
            member=active_member(role="admin"),
            session=AsyncMock(),
        )

    assert exc_info.value.status_code == 404
