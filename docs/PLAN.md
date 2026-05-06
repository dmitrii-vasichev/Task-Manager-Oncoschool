# Task Labels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional team-wide multi-label grouping and filtering for web portal tasks without changing existing task visibility rules.

**Architecture:** Introduce a normalized `task_labels` catalog plus a `task_label_links` many-to-many table. Backend APIs create/search labels, task create/update accepts `label_ids`, and task listing applies label filters after existing department/role visibility. The frontend adds a reusable `TaskLabelPicker`, label chips on task cards/detail, and label filtering on the tasks board.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic, unittest/pytest, Next.js 14, TypeScript, Tailwind, shadcn/Radix primitives, lucide-react.

---

## Source Documents

- Approved design spec: `docs/superpowers/specs/2026-05-05-task-labels-design.md`
- Existing task API: `backend/app/api/tasks.py`
- Existing task domain model: `backend/app/db/models.py`
- Existing task schemas: `backend/app/db/schemas.py`
- Existing task board: `frontend/src/app/tasks/page.tsx`
- Existing task components: `frontend/src/components/tasks/`

## Scope Check

This plan covers one subsystem: web task labels. It does not include Telegram bot support, task analytics by label, private labels, or a moderator label-management UI. The data model stores enough metadata for those future additions, but every task below produces working, testable web-label behavior on its own path.

## File Structure

Backend files:

- Create `backend/alembic/versions/029_task_labels.py`: migration for `task_labels` and `task_label_links`.
- Modify `backend/app/db/models.py`: add `TaskLabel`, `TaskLabelLink`, and `Task.labels`.
- Modify `backend/app/db/schemas.py`: add label request/response schemas and task `label_ids`/`labels`.
- Modify `backend/app/db/repositories.py`: add label repository methods and task label loading/filter helpers.
- Modify `backend/app/services/permission_service.py`: allow `label_ids` for every user who can edit a task.
- Modify `backend/app/services/task_service.py`: pass optional `label_ids` on task creation.
- Create `backend/app/api/task_labels.py`: label search/create endpoints.
- Modify `backend/app/api/router.py`: register label router.
- Modify `backend/app/api/tasks.py`: parse label filters and replace labels on create/update.
- Create `backend/tests/test_task_label_repository.py`: label normalization/catalog behavior.
- Create `backend/tests/test_task_label_api.py`: label endpoint behavior.
- Modify `backend/tests/test_task_permission_service.py`: permission matrix includes `label_ids`.
- Modify `backend/tests/test_task_update_permissions.py`: label update permission regression tests.

Frontend files:

- Modify `frontend/src/lib/types.ts`: add `TaskLabel`, task labels, request label IDs, and filter values.
- Modify `frontend/src/lib/api.ts`: add label API methods and task query serialization support.
- Create `frontend/src/components/tasks/TaskLabelPicker.tsx`: reusable multi-select/create field.
- Create `frontend/src/components/tasks/TaskLabelChips.tsx`: compact label display and overflow chip.
- Modify `frontend/src/components/tasks/TaskFilters.tsx`: add label filter.
- Modify `frontend/src/components/tasks/TaskCard.tsx`: show compact label chips.
- Modify `frontend/src/components/tasks/CreateTaskDialog.tsx`: select/create labels during task creation.
- Modify `frontend/src/app/tasks/page.tsx`: store label filters and pass `label_ids`.
- Modify `frontend/src/app/tasks/[id]/page.tsx`: show and edit labels in task detail.

---

## Task 1: Backend Label Schema, Models, and Repository

**Files:**

- Create: `backend/alembic/versions/029_task_labels.py`
- Modify: `backend/app/db/models.py`
- Modify: `backend/app/db/schemas.py`
- Modify: `backend/app/db/repositories.py`
- Test: `backend/tests/test_task_label_repository.py`

- [ ] **Step 1: Write failing model and repository tests**

Create `backend/tests/test_task_label_repository.py`:

```python
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.db.models import Task, TaskLabel, TaskLabelLink
from app.db.repositories import (
    LABEL_COLOR_PALETTE,
    TaskLabelRepository,
    normalize_task_label_name,
    slugify_task_label,
)


class TaskLabelModelTests(unittest.TestCase):
    def test_task_label_columns_exist(self) -> None:
        columns = TaskLabel.__table__.columns
        self.assertIn("name", columns)
        self.assertIn("slug", columns)
        self.assertIn("color", columns)
        self.assertIn("created_by_id", columns)
        self.assertIn("is_archived", columns)

    def test_task_label_link_columns_exist(self) -> None:
        columns = TaskLabelLink.__table__.columns
        self.assertIn("task_id", columns)
        self.assertIn("label_id", columns)
        self.assertIn("created_at", columns)

    def test_task_has_labels_relationship(self) -> None:
        self.assertTrue(hasattr(Task, "labels"))


class TaskLabelNormalizationTests(unittest.TestCase):
    def test_normalize_label_name_trims_and_collapses_spaces(self) -> None:
        self.assertEqual(normalize_task_label_name("  VK   Launch  "), "VK Launch")

    def test_normalize_label_name_rejects_empty(self) -> None:
        with self.assertRaises(ValueError):
            normalize_task_label_name("   ")

    def test_normalize_label_name_rejects_long_names(self) -> None:
        with self.assertRaises(ValueError):
            normalize_task_label_name("x" * 81)

    def test_slugify_label_is_case_insensitive(self) -> None:
        self.assertEqual(slugify_task_label(" VK Launch "), slugify_task_label("vk launch"))

    def test_palette_is_non_empty(self) -> None:
        self.assertGreater(len(LABEL_COLOR_PALETTE), 0)


class TaskLabelRepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_or_reactivate_returns_existing_active_label(self) -> None:
        existing = SimpleNamespace(
            id=uuid.uuid4(),
            name="Conference",
            slug="conference",
            color="teal",
            is_archived=False,
        )
        session = MagicMock()
        repo = TaskLabelRepository()
        repo.get_by_slug = AsyncMock(return_value=existing)

        result = await repo.create_or_reactivate(
            session,
            name=" conference ",
            created_by_id=uuid.uuid4(),
        )

        self.assertIs(result, existing)
        session.add.assert_not_called()

    async def test_create_or_reactivate_unarchives_existing_label(self) -> None:
        archived = SimpleNamespace(
            id=uuid.uuid4(),
            name="Conference",
            slug="conference",
            color="teal",
            is_archived=True,
        )
        session = MagicMock()
        session.flush = AsyncMock()
        repo = TaskLabelRepository()
        repo.get_by_slug = AsyncMock(return_value=archived)

        result = await repo.create_or_reactivate(
            session,
            name="Conference",
            created_by_id=uuid.uuid4(),
        )

        self.assertIs(result, archived)
        self.assertFalse(archived.is_archived)
        session.flush.assert_awaited_once()
```

- [ ] **Step 2: Run the focused failing tests**

Run:

```bash
cd backend
pytest tests/test_task_label_repository.py -q
```

Expected: FAIL with import/name errors for `TaskLabel`, `TaskLabelLink`, `TaskLabelRepository`, and label normalization helpers.

- [ ] **Step 3: Add Alembic migration**

Create `backend/alembic/versions/029_task_labels.py`:

```python
"""Add task labels

Revision ID: 029
Revises: 028
Create Date: 2026-05-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "029"
down_revision: Union[str, None] = "028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "task_labels",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("color", sa.String(30), nullable=False),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("team_members.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_task_labels_slug"),
    )
    op.create_index("idx_task_labels_is_archived", "task_labels", ["is_archived"])
    op.create_index("idx_task_labels_created_at", "task_labels", ["created_at"])

    op.create_table(
        "task_label_links",
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "label_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("task_labels.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_task_label_links_label_id", "task_label_links", ["label_id"])
    op.create_index("idx_task_label_links_task_id", "task_label_links", ["task_id"])


def downgrade() -> None:
    op.drop_index("idx_task_label_links_task_id", table_name="task_label_links")
    op.drop_index("idx_task_label_links_label_id", table_name="task_label_links")
    op.drop_table("task_label_links")
    op.drop_index("idx_task_labels_created_at", table_name="task_labels")
    op.drop_index("idx_task_labels_is_archived", table_name="task_labels")
    op.drop_table("task_labels")
```

- [ ] **Step 4: Add SQLAlchemy models**

Modify `backend/app/db/models.py`.

Add `ForeignKeyConstraint` is not needed. Keep the existing imports and add these classes before `class Task(Base)`:

```python
class TaskLabel(Base):
    __tablename__ = "task_labels"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_task_labels_slug"),
        Index("idx_task_labels_is_archived", "is_archived"),
        Index("idx_task_labels_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(30), nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("team_members.id", ondelete="SET NULL"), nullable=True
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    tasks: Mapped[list["Task"]] = relationship(
        secondary="task_label_links",
        back_populates="labels",
    )


class TaskLabelLink(Base):
    __tablename__ = "task_label_links"
    __table_args__ = (
        Index("idx_task_label_links_label_id", "label_id"),
        Index("idx_task_label_links_task_id", "task_id"),
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
    label_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("task_labels.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
```

Inside `Task`, add the relationship near `updates`:

```python
    labels: Mapped[list["TaskLabel"]] = relationship(
        secondary="task_label_links",
        back_populates="tasks",
    )
```

- [ ] **Step 5: Add Pydantic schemas**

Modify `backend/app/db/schemas.py`.

Add below `TaskChecklistItem`:

```python
class TaskLabelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class TaskLabelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    color: str
    created_by_id: uuid.UUID | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    usage_count: int = 0
```

Add to `TaskCreate`:

```python
    label_ids: list[uuid.UUID] = Field(default_factory=list)
```

Add to `TaskEdit`:

```python
    label_ids: list[uuid.UUID] | None = None
```

Add to `TaskResponse`:

```python
    labels: list[TaskLabelResponse] = Field(default_factory=list)
```

- [ ] **Step 6: Add repository helpers**

Modify `backend/app/db/repositories.py`.

Add `TaskLabel` and `TaskLabelLink` to the model imports.

Add helpers near the top of the file:

```python
import re

LABEL_COLOR_PALETTE = (
    "teal",
    "coral",
    "blue",
    "purple",
    "gold",
    "green",
    "slate",
)


def normalize_task_label_name(raw_name: str) -> str:
    normalized = re.sub(r"\s+", " ", raw_name or "").strip()
    if not normalized:
        raise ValueError("Название метки не может быть пустым")
    if len(normalized) > 80:
        raise ValueError("Название метки не может быть длиннее 80 символов")
    return normalized


def slugify_task_label(raw_name: str) -> str:
    return normalize_task_label_name(raw_name).casefold()


def pick_task_label_color(slug: str) -> str:
    index = sum(ord(char) for char in slug) % len(LABEL_COLOR_PALETTE)
    return LABEL_COLOR_PALETTE[index]
```

Add repository class before `TaskRepository`:

```python
class TaskLabelRepository:
    async def get_by_slug(self, session: AsyncSession, slug: str) -> TaskLabel | None:
        stmt = select(TaskLabel).where(TaskLabel.slug == slug)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(
        self, session: AsyncSession, label_ids: list[uuid.UUID]
    ) -> list[TaskLabel]:
        if not label_ids:
            return []
        stmt = select(TaskLabel).where(TaskLabel.id.in_(label_ids))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def search(
        self,
        session: AsyncSession,
        search: str | None = None,
        include_archived: bool = False,
        limit: int = 20,
    ) -> list[tuple[TaskLabel, int]]:
        usage_count = func.count(TaskLabelLink.task_id).label("usage_count")
        stmt = (
            select(TaskLabel, usage_count)
            .outerjoin(TaskLabelLink, TaskLabelLink.label_id == TaskLabel.id)
            .group_by(TaskLabel.id)
            .order_by(usage_count.desc(), TaskLabel.name.asc())
            .limit(limit)
        )
        if not include_archived:
            stmt = stmt.where(TaskLabel.is_archived.is_(False))
        if search:
            normalized = normalize_task_label_name(search)
            stmt = stmt.where(TaskLabel.name.ilike(f"%{normalized}%"))
        result = await session.execute(stmt)
        return [(row[0], int(row[1] or 0)) for row in result.all()]

    async def create_or_reactivate(
        self,
        session: AsyncSession,
        *,
        name: str,
        created_by_id: uuid.UUID | None,
    ) -> TaskLabel:
        normalized = normalize_task_label_name(name)
        slug = slugify_task_label(normalized)
        existing = await self.get_by_slug(session, slug)
        if existing:
            if existing.is_archived:
                existing.is_archived = False
                existing.name = normalized
                await session.flush()
            return existing
        label = TaskLabel(
            name=normalized,
            slug=slug,
            color=pick_task_label_color(slug),
            created_by_id=created_by_id,
        )
        session.add(label)
        await session.flush()
        return label

    async def replace_task_labels(
        self,
        session: AsyncSession,
        task: Task,
        label_ids: list[uuid.UUID],
    ) -> Task:
        labels = await self.get_by_ids(session, label_ids)
        found_ids = {label.id for label in labels}
        missing_ids = [label_id for label_id in label_ids if label_id not in found_ids]
        if missing_ids:
            raise ValueError("Одна или несколько меток не найдены")
        task.labels = labels
        await session.flush()
        return task
```

Update `TaskRepository.get_by_id`, `get_by_short_id`, `get_by_assignee`, and `get_all_active` options to preload labels:

```python
.options(
    selectinload(Task.assignee),
    selectinload(Task.created_by),
    selectinload(Task.labels),
)
```

- [ ] **Step 7: Run focused tests**

Run:

```bash
cd backend
pytest tests/test_task_label_repository.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit backend schema foundation**

```bash
git add backend/alembic/versions/029_task_labels.py backend/app/db/models.py backend/app/db/schemas.py backend/app/db/repositories.py backend/tests/test_task_label_repository.py
git commit -m "feat: add task label data model"
```

---

## Task 2: Backend Label API

**Files:**

- Create: `backend/app/api/task_labels.py`
- Modify: `backend/app/api/router.py`
- Test: `backend/tests/test_task_label_api.py`

- [ ] **Step 1: Write failing API unit tests**

Create `backend/tests/test_task_label_api.py`:

```python
import unittest
import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.api import task_labels as labels_api


def make_label(name: str = "Conference", usage_count: int = 3) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        name=name,
        slug=name.casefold(),
        color="teal",
        created_by_id=uuid.uuid4(),
        is_archived=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        usage_count=usage_count,
    )


class TaskLabelApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_list_task_labels_returns_usage_count(self) -> None:
        label = make_label()
        member = SimpleNamespace(id=uuid.uuid4(), role="member", is_active=True)
        session = SimpleNamespace()

        with patch.object(
            labels_api.label_repo,
            "search",
            AsyncMock(return_value=[(label, 3)]),
        ) as search_mock:
            response = await labels_api.list_task_labels(
                search="conf",
                limit=20,
                include_archived=False,
                member=member,
                session=session,
            )

        self.assertEqual(response[0].id, label.id)
        self.assertEqual(response[0].usage_count, 3)
        search_mock.assert_awaited_once_with(
            session,
            search="conf",
            include_archived=False,
            limit=20,
        )

    async def test_create_task_label_commits_and_returns_label(self) -> None:
        label = make_label("Partners", usage_count=0)
        member = SimpleNamespace(id=uuid.uuid4(), role="member", is_active=True)
        session = SimpleNamespace(commit=AsyncMock())

        with patch.object(
            labels_api.label_repo,
            "create_or_reactivate",
            AsyncMock(return_value=label),
        ) as create_mock:
            response = await labels_api.create_task_label(
                data=labels_api.TaskLabelCreate(name=" Partners "),
                member=member,
                session=session,
            )

        self.assertEqual(response.name, "Partners")
        self.assertEqual(response.usage_count, 0)
        create_mock.assert_awaited_once_with(
            session,
            name=" Partners ",
            created_by_id=member.id,
        )
        session.commit.assert_awaited_once()
```

- [ ] **Step 2: Run API tests to verify failure**

Run:

```bash
cd backend
pytest tests/test_task_label_api.py -q
```

Expected: FAIL because `app.api.task_labels` does not exist.

- [ ] **Step 3: Implement label router**

Create `backend/app/api/task_labels.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.db.database import get_session
from app.db.models import TeamMember
from app.db.repositories import TaskLabelRepository
from app.db.schemas import TaskLabelCreate, TaskLabelResponse

router = APIRouter(prefix="/task-labels", tags=["task-labels"])
label_repo = TaskLabelRepository()


def _label_response(label, usage_count: int = 0) -> TaskLabelResponse:
    return TaskLabelResponse.model_validate(label).model_copy(
        update={"usage_count": usage_count}
    )


@router.get("", response_model=list[TaskLabelResponse])
async def list_task_labels(
    search: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    include_archived: bool = Query(False),
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    labels = await label_repo.search(
        session,
        search=search,
        include_archived=include_archived,
        limit=limit,
    )
    return [_label_response(label, usage_count) for label, usage_count in labels]


@router.post("", response_model=TaskLabelResponse, status_code=201)
async def create_task_label(
    data: TaskLabelCreate,
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        label = await label_repo.create_or_reactivate(
            session,
            name=data.name,
            created_by_id=member.id,
        )
        await session.commit()
        return _label_response(label, 0)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
```

- [ ] **Step 4: Register label router**

Modify `backend/app/api/router.py`:

```python
from app.api.task_labels import router as task_labels_router
```

Add after task routes:

```python
api_router.include_router(task_labels_router)
```

- [ ] **Step 5: Run focused API tests**

Run:

```bash
cd backend
pytest tests/test_task_label_api.py -q
```

Expected: PASS.

- [ ] **Step 6: Run backend label tests**

Run:

```bash
cd backend
pytest tests/test_task_label_repository.py tests/test_task_label_api.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit label API**

```bash
git add backend/app/api/task_labels.py backend/app/api/router.py backend/tests/test_task_label_api.py
git commit -m "feat: add task label API"
```

---

## Task 3: Integrate Labels into Task Backend

**Files:**

- Modify: `backend/app/services/permission_service.py`
- Modify: `backend/app/services/task_service.py`
- Modify: `backend/app/api/tasks.py`
- Modify: `backend/app/db/repositories.py`
- Modify: `backend/tests/test_task_permission_service.py`
- Modify: `backend/tests/test_task_update_permissions.py`
- Test: `backend/tests/test_task_label_task_api.py`

- [ ] **Step 1: Update permission tests first**

Modify expected field sets in `backend/tests/test_task_permission_service.py`.

Assignee member expected set:

```python
{
    "status",
    "checklist",
    "title",
    "label_ids",
    "reminder_at",
    "reminder_comment",
}
```

Author member expected set:

```python
{
    "status",
    "checklist",
    "title",
    "label_ids",
    "description",
    "priority",
    "deadline",
    "assignee_id",
}
```

Moderator expected set:

```python
{
    "status",
    "checklist",
    "title",
    "label_ids",
    "description",
    "priority",
    "deadline",
    "assignee_id",
    "reminder_at",
    "reminder_comment",
}
```

- [ ] **Step 2: Add task update permission regression tests**

Append to `backend/tests/test_task_update_permissions.py`:

```python
    async def test_member_assignee_can_update_labels(self) -> None:
        member_id = uuid.uuid4()
        label_ids = [uuid.uuid4(), uuid.uuid4()]
        task = SimpleNamespace(
            id=uuid.uuid4(),
            assignee_id=member_id,
            created_by_id=uuid.uuid4(),
            status="new",
            assignee=None,
            labels=[],
        )
        updated_task = SimpleNamespace(id=task.id, labels=[])
        member = SimpleNamespace(id=member_id, role="member")
        session = SimpleNamespace(commit=AsyncMock())
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(bot=None)))

        with patch.object(
            tasks_api.task_service,
            "get_task_by_short_id",
            AsyncMock(return_value=task),
        ), patch.object(
            tasks_api,
            "can_access_task",
            AsyncMock(return_value=True),
        ), patch.object(
            tasks_api.label_repo,
            "replace_task_labels",
            AsyncMock(return_value=updated_task),
        ) as replace_mock:
            response = await tasks_api.update_task(
                request=request,
                short_id=101,
                data=tasks_api.TaskEdit(label_ids=label_ids),
                member=member,
                session=session,
            )

        self.assertIs(response, updated_task)
        replace_mock.assert_awaited_once_with(session, task, label_ids)
        session.commit.assert_awaited_once()

    async def test_unrelated_member_cannot_update_labels(self) -> None:
        task = SimpleNamespace(
            id=uuid.uuid4(),
            assignee_id=uuid.uuid4(),
            created_by_id=uuid.uuid4(),
            status="new",
            assignee=None,
            labels=[],
        )
        member = SimpleNamespace(id=uuid.uuid4(), role="member")
        session = SimpleNamespace(commit=AsyncMock())
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(bot=None)))

        with patch.object(
            tasks_api.task_service,
            "get_task_by_short_id",
            AsyncMock(return_value=task),
        ), patch.object(
            tasks_api,
            "can_access_task",
            AsyncMock(return_value=True),
        ), patch.object(
            tasks_api.label_repo,
            "replace_task_labels",
            AsyncMock(),
        ) as replace_mock:
            with self.assertRaises(HTTPException) as ctx:
                await tasks_api.update_task(
                    request=request,
                    short_id=101,
                    data=tasks_api.TaskEdit(label_ids=[uuid.uuid4()]),
                    member=member,
                    session=session,
                )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("Нет прав", str(ctx.exception.detail))
        replace_mock.assert_not_awaited()
        session.commit.assert_not_awaited()
```

- [ ] **Step 3: Add task API label behavior tests**

Create `backend/tests/test_task_label_task_api.py`:

```python
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.api import tasks as tasks_api


class TaskLabelTaskApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_task_replaces_labels_after_task_creation(self) -> None:
        label_ids = [uuid.uuid4()]
        member = SimpleNamespace(id=uuid.uuid4(), role="member")
        task = SimpleNamespace(id=uuid.uuid4(), assignee_id=member.id, labels=[])
        labeled_task = SimpleNamespace(id=task.id, labels=[])
        session = SimpleNamespace(commit=AsyncMock())
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(bot=None)))

        with patch.object(
            tasks_api.task_service,
            "create_task",
            AsyncMock(return_value=task),
        ) as create_mock, patch.object(
            tasks_api.label_repo,
            "replace_task_labels",
            AsyncMock(return_value=labeled_task),
        ) as replace_mock:
            response = await tasks_api.create_task(
                request=request,
                data=tasks_api.TaskCreate(title="Task", label_ids=label_ids),
                member=member,
                session=session,
            )

        self.assertIs(response, labeled_task)
        create_mock.assert_awaited_once()
        replace_mock.assert_awaited_once_with(session, task, label_ids)
        session.commit.assert_awaited_once()

    async def test_parse_label_ids_csv(self) -> None:
        first = uuid.uuid4()
        second = uuid.uuid4()
        self.assertEqual(
            tasks_api._parse_label_ids_filter(f"{first},{second}"),
            [first, second],
        )

    async def test_parse_label_ids_empty_string(self) -> None:
        self.assertEqual(tasks_api._parse_label_ids_filter(""), [])

    async def test_apply_label_filter_joins_labels(self) -> None:
        stmt = MagicMock()
        joined = MagicMock()
        filtered = MagicMock()
        distinct_stmt = MagicMock()
        stmt.join.return_value = joined
        joined.where.return_value = filtered
        filtered.distinct.return_value = distinct_stmt
        label_id = uuid.uuid4()

        result = tasks_api._apply_label_filter(stmt, [label_id])

        self.assertIs(result, distinct_stmt)
        stmt.join.assert_called_once()
        joined.where.assert_called_once()
        filtered.distinct.assert_called_once()
```

- [ ] **Step 4: Run focused backend tests to verify failure**

Run:

```bash
cd backend
pytest tests/test_task_permission_service.py tests/test_task_update_permissions.py tests/test_task_label_task_api.py -q
```

Expected: FAIL because permission fields, `label_repo`, and label helpers are not integrated.

- [ ] **Step 5: Update task permissions**

Modify `backend/app/services/permission_service.py`:

```python
    TASK_EDIT_BASE_FIELDS = {"status", "checklist", "title", "label_ids"}
```

- [ ] **Step 6: Update task service creation signature**

Modify `backend/app/services/task_service.py`.

Add parameter:

```python
        label_ids: list[uuid.UUID] | None = None,
```

After task creation:

```python
        if label_ids:
            from app.db.repositories import TaskLabelRepository

            task = await TaskLabelRepository().replace_task_labels(
                session,
                task,
                label_ids,
            )
```

Keep the default `None` so Telegram and bot flows keep working unchanged.

- [ ] **Step 7: Update task API imports and helpers**

Modify `backend/app/api/tasks.py`.

Add imports:

```python
from app.db.models import Task, TaskLabel, TeamMember
from app.db.repositories import TaskLabelRepository
```

Add module global:

```python
label_repo = TaskLabelRepository()
```

Add helpers above `list_tasks`:

```python
def _parse_label_ids_filter(raw_value: str | None) -> list[uuid.UUID]:
    if not raw_value:
        return []
    parsed: list[uuid.UUID] = []
    for raw_part in raw_value.split(","):
        value = raw_part.strip()
        if not value:
            continue
        parsed.append(uuid.UUID(value))
    return parsed


def _apply_label_filter(stmt, label_ids: list[uuid.UUID]):
    if not label_ids:
        return stmt
    return stmt.join(Task.labels).where(TaskLabel.id.in_(label_ids)).distinct()
```

- [ ] **Step 8: Update task list endpoint**

In `list_tasks`, add query parameter:

```python
    label_ids: str | None = Query(None),
```

After source/search filters:

```python
    try:
        parsed_label_ids = _parse_label_ids_filter(label_ids)
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректный идентификатор метки")
    base_stmt = _apply_label_filter(base_stmt, parsed_label_ids)
```

Add label preload to `items_stmt`:

```python
.options(
    selectinload(Task.assignee),
    selectinload(Task.created_by),
    selectinload(Task.labels),
)
```

- [ ] **Step 9: Update task create endpoint**

In `create_task`, pass labels into service:

```python
            label_ids=data.label_ids,
```

No API-level replacement is needed here because Step 6 makes `TaskService.create_task()` responsible for attaching labels.

- [ ] **Step 10: Update task patch endpoint**

In `update_task`, exclude `label_ids` from scalar update fields:

```python
        update_fields = data.model_dump(
            exclude_unset=True,
            exclude={"status", "reminder_at", "reminder_comment", "label_ids"},
        )
```

Before final commit:

```python
        payload = data.model_dump(exclude_unset=True)
        if "label_ids" in payload:
            task = await label_repo.replace_task_labels(
                session,
                task,
                data.label_ids or [],
            )
```

- [ ] **Step 11: Run focused backend tests**

Run:

```bash
cd backend
pytest tests/test_task_permission_service.py tests/test_task_update_permissions.py tests/test_task_label_task_api.py tests/test_task_label_api.py tests/test_task_label_repository.py -q
```

Expected: PASS.

- [ ] **Step 12: Commit task backend integration**

```bash
git add backend/app/services/permission_service.py backend/app/services/task_service.py backend/app/api/tasks.py backend/app/db/repositories.py backend/tests/test_task_permission_service.py backend/tests/test_task_update_permissions.py backend/tests/test_task_label_task_api.py
git commit -m "feat: attach labels to tasks"
```

---

## Task 4: Frontend Types, API Client, and Reusable Label Components

**Files:**

- Modify: `frontend/src/lib/types.ts`
- Modify: `frontend/src/lib/api.ts`
- Create: `frontend/src/components/tasks/TaskLabelChips.tsx`
- Create: `frontend/src/components/tasks/TaskLabelPicker.tsx`

- [ ] **Step 1: Update TypeScript types**

Modify `frontend/src/lib/types.ts`.

Add model:

```ts
export interface TaskLabel {
  id: string;
  name: string;
  slug: string;
  color: string;
  created_by_id: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  usage_count: number;
}
```

Add to `Task`:

```ts
  labels: TaskLabel[];
```

Add to `TaskCreateRequest`:

```ts
  label_ids?: string[];
```

Add to `TaskEditRequest`:

```ts
  label_ids?: string[];
```

Add request type:

```ts
export interface TaskLabelCreateRequest {
  name: string;
}
```

- [ ] **Step 2: Update API client**

Modify `frontend/src/lib/api.ts`.

Add imported type:

```ts
  TaskLabel,
  TaskLabelCreateRequest,
```

Add methods in the Tasks section:

```ts
  async getTaskLabels(params?: {
    search?: string;
    limit?: number;
  }): Promise<TaskLabel[]> {
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.set("search", params.search);
    if (params?.limit) searchParams.set("limit", String(params.limit));
    const query = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return this.request<TaskLabel[]>(`/api/task-labels${query}`);
  }

  async createTaskLabel(data: TaskLabelCreateRequest): Promise<TaskLabel> {
    return this.request<TaskLabel>("/api/task-labels", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }
```

- [ ] **Step 3: Add compact label chip component**

Create `frontend/src/components/tasks/TaskLabelChips.tsx`:

```tsx
"use client";

import type { TaskLabel } from "@/lib/types";
import { cn } from "@/lib/utils";

const LABEL_CLASSES: Record<string, string> = {
  teal: "bg-primary/12 text-primary border-primary/20",
  coral: "bg-accent/12 text-accent border-accent/20",
  blue: "bg-blue-500/10 text-blue-700 border-blue-500/20 dark:text-blue-300",
  purple: "bg-purple-500/10 text-purple-700 border-purple-500/20 dark:text-purple-300",
  gold: "bg-amber-500/12 text-amber-700 border-amber-500/20 dark:text-amber-300",
  green: "bg-emerald-500/10 text-emerald-700 border-emerald-500/20 dark:text-emerald-300",
  slate: "bg-slate-500/10 text-slate-700 border-slate-500/20 dark:text-slate-300",
};

function labelClass(color: string) {
  return LABEL_CLASSES[color] || LABEL_CLASSES.slate;
}

export function TaskLabelChips({
  labels,
  maxVisible = 2,
  className,
}: {
  labels: TaskLabel[];
  maxVisible?: number;
  className?: string;
}) {
  if (!labels.length) return null;

  const visible = labels.slice(0, maxVisible);
  const hiddenCount = labels.length - visible.length;

  return (
    <div className={cn("flex min-w-0 flex-wrap gap-1.5", className)}>
      {visible.map((label) => (
        <span
          key={label.id}
          className={cn(
            "inline-flex max-w-full items-center rounded-full border px-2 py-0.5 text-2xs font-medium leading-4",
            labelClass(label.color)
          )}
          title={label.name}
        >
          <span className="truncate">{label.name}</span>
        </span>
      ))}
      {hiddenCount > 0 && (
        <span className="inline-flex items-center rounded-full border border-border/60 bg-muted px-2 py-0.5 text-2xs font-medium text-muted-foreground">
          +{hiddenCount}
        </span>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Add label picker component**

Create `frontend/src/components/tasks/TaskLabelPicker.tsx`:

```tsx
"use client";

import { useEffect, useMemo, useState } from "react";
import { Check, Loader2, Plus, Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { api } from "@/lib/api";
import type { TaskLabel } from "@/lib/types";
import { TaskLabelChips } from "./TaskLabelChips";

export function TaskLabelPicker({
  value,
  onChange,
  disabled = false,
  placeholder = "Метки",
}: {
  value: TaskLabel[];
  onChange: (labels: TaskLabel[]) => void;
  disabled?: boolean;
  placeholder?: string;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [options, setOptions] = useState<TaskLabel[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const selectedIds = useMemo(() => new Set(value.map((label) => label.id)), [value]);
  const normalizedSearch = search.trim();
  const canCreate =
    normalizedSearch.length > 0 &&
    !options.some((label) => label.name.toLowerCase() === normalizedSearch.toLowerCase());

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setLoading(true);
    api
      .getTaskLabels({ search: normalizedSearch || undefined, limit: 20 })
      .then((labels) => {
        if (!cancelled) setOptions(labels);
      })
      .catch(() => {
        if (!cancelled) setOptions([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, normalizedSearch]);

  function toggleLabel(label: TaskLabel) {
    if (selectedIds.has(label.id)) {
      onChange(value.filter((item) => item.id !== label.id));
      return;
    }
    onChange([...value, label]);
  }

  async function createLabel() {
    if (!normalizedSearch || creating) return;
    setCreating(true);
    try {
      const label = await api.createTaskLabel({ name: normalizedSearch });
      if (!selectedIds.has(label.id)) {
        onChange([...value, label]);
      }
      setSearch("");
      setOpen(false);
    } finally {
      setCreating(false);
    }
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          disabled={disabled}
          className="h-auto min-h-10 w-full justify-start gap-2 px-3 py-2"
        >
          {value.length ? (
            <TaskLabelChips labels={value} maxVisible={3} />
          ) : (
            <span className="text-muted-foreground">{placeholder}</span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="start" className="w-[320px] p-2">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Найти или создать метку"
            className="h-9 pl-9"
          />
        </div>
        <div className="mt-2 max-h-64 overflow-y-auto">
          {loading && (
            <div className="flex items-center gap-2 px-2 py-3 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Загрузка...
            </div>
          )}
          {!loading &&
            options.map((label) => (
              <button
                key={label.id}
                type="button"
                onClick={() => toggleLabel(label)}
                className="flex w-full items-center justify-between rounded-md px-2 py-2 text-left text-sm hover:bg-muted"
              >
                <span className="truncate">{label.name}</span>
                <span className="flex items-center gap-2 text-xs text-muted-foreground">
                  {label.usage_count}
                  {selectedIds.has(label.id) && <Check className="h-4 w-4 text-primary" />}
                </span>
              </button>
            ))}
          {!loading && canCreate && (
            <button
              type="button"
              onClick={() => void createLabel()}
              disabled={creating}
              className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-sm font-medium text-primary hover:bg-primary/10"
            >
              {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              Создать "{normalizedSearch}"
            </button>
          )}
        </div>
        {value.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5 border-t border-border/60 pt-2">
            {value.map((label) => (
              <button
                key={label.id}
                type="button"
                onClick={() => onChange(value.filter((item) => item.id !== label.id))}
                className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-1 text-xs"
              >
                {label.name}
                <X className="h-3 w-3" />
              </button>
            ))}
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
```

- [ ] **Step 5: Run TypeScript check**

```bash
cd frontend
npx tsc --noEmit
```

Expected: PASS.

- [ ] **Step 6: Commit frontend label foundation**

```bash
git add frontend/src/lib/types.ts frontend/src/lib/api.ts frontend/src/components/tasks/TaskLabelChips.tsx frontend/src/components/tasks/TaskLabelPicker.tsx
git commit -m "feat: add task label frontend primitives"
```

---

## Task 5: Task Board Label Filter and Card Display

**Files:**

- Modify: `frontend/src/components/tasks/TaskFilters.tsx`
- Modify: `frontend/src/components/tasks/TaskCard.tsx`
- Modify: `frontend/src/app/tasks/page.tsx`

- [ ] **Step 1: Extend filter state**

Modify `TaskFilterValues` in `frontend/src/components/tasks/TaskFilters.tsx`:

```ts
export interface TaskFilterValues {
  search: string;
  priority: string;
  source: string;
  department_id: string;
  assignee_id: string;
  created_by_id: string;
  labels: TaskLabel[];
}
```

Update `EMPTY_FILTERS`:

```ts
export const EMPTY_FILTERS: TaskFilterValues = {
  search: "",
  priority: "",
  source: "",
  department_id: "",
  assignee_id: "",
  created_by_id: "",
  labels: [],
};
```

Import `TaskLabel` and `TaskLabelPicker`:

```ts
import { TaskLabelPicker } from "@/components/tasks/TaskLabelPicker";
import type { Department, TaskLabel, TeamMember } from "@/lib/types";
```

- [ ] **Step 2: Add active label filter chips**

In `TaskFilters`, after source active filter handling:

```ts
if (filters.labels.length > 0) {
  activeFilters.push({
    key: "labels",
    label:
      filters.labels.length === 1
        ? `Метка: ${filters.labels[0].name}`
        : `Метки: ${filters.labels.length}`,
  });
}
```

Update `removeFilter`:

```ts
function removeFilter(key: keyof TaskFilterValues) {
  onFiltersChange({
    ...filters,
    [key]: key === "labels" ? [] : "",
  });
}
```

- [ ] **Step 3: Add label picker to filter row**

In the desktop filters group, after Source:

```tsx
          <div className="w-full shrink-0 sm:w-[190px] lg:w-[190px]">
            <TaskLabelPicker
              value={filters.labels}
              onChange={(labels) => onFiltersChange({ ...filters, labels })}
              placeholder="Все метки"
            />
          </div>
```

- [ ] **Step 4: Update task page query params**

Modify `frontend/src/app/tasks/page.tsx`.

When building `params`, add:

```ts
      if (filters.labels.length > 0) {
        params.label_ids = filters.labels.map((label) => label.id).join(",");
      }
```

Add `filters.labels` to the `fetchData` dependency list.

The local `filteredTasks` does not need a label filter because the backend already filters. Leave local search/priority/source checks as they are.

- [ ] **Step 5: Display label chips on cards**

Modify `frontend/src/components/tasks/TaskCard.tsx`.

Import:

```ts
import { TaskLabelChips } from "@/components/tasks/TaskLabelChips";
```

After the source icon row and before checklist preview:

```tsx
            <TaskLabelChips labels={task.labels || []} maxVisible={2} />
```

This returns `null` for unlabeled tasks, so ordinary cards keep their current visual density.

- [ ] **Step 6: Run frontend verification**

Run:

```bash
cd frontend
npx tsc --noEmit
```

Expected: PASS.

- [ ] **Step 7: Commit board filter and chips**

```bash
git add frontend/src/components/tasks/TaskFilters.tsx frontend/src/components/tasks/TaskCard.tsx frontend/src/app/tasks/page.tsx
git commit -m "feat: filter task board by labels"
```

---

## Task 6: Create Task and Task Detail Label Editing

**Files:**

- Modify: `frontend/src/components/tasks/CreateTaskDialog.tsx`
- Modify: `frontend/src/app/tasks/[id]/page.tsx`

- [ ] **Step 1: Add labels to create dialog state**

Modify `frontend/src/components/tasks/CreateTaskDialog.tsx`.

Imports:

```ts
import { TaskLabelPicker } from "@/components/tasks/TaskLabelPicker";
import type { TaskLabel, TeamMember, TaskPriority } from "@/lib/types";
```

Add state:

```ts
  const [labels, setLabels] = useState<TaskLabel[]>([]);
```

Reset it:

```ts
    setLabels([]);
```

Send `label_ids`:

```ts
        label_ids: labels.map((label) => label.id),
```

- [ ] **Step 2: Add create dialog field**

Add this field after Description and before Priority:

```tsx
          <div className="space-y-2">
            <Label className="text-sm font-medium">Метки</Label>
            <TaskLabelPicker
              value={labels}
              onChange={setLabels}
              disabled={saving}
              placeholder="Добавить метки"
            />
          </div>
```

- [ ] **Step 3: Add task detail label state**

Modify `frontend/src/app/tasks/[id]/page.tsx`.

Imports:

```ts
import { TaskLabelPicker } from "@/components/tasks/TaskLabelPicker";
import { TaskLabelChips } from "@/components/tasks/TaskLabelChips";
import type { TaskLabel, TaskStatus, TaskPriority, TaskChecklistItem } from "@/lib/types";
```

Add state near other editing state:

```ts
  const [labelDraft, setLabelDraft] = useState<TaskLabel[]>([]);
  const [savingLabels, setSavingLabels] = useState(false);
```

Sync with loaded task:

```ts
  useEffect(() => {
    if (!task) return;
    setLabelDraft(task.labels || []);
  }, [task]);
```

Add permission:

```ts
  const canEditLabels = !!user && PermissionService.canEditTask(user, task);
```

Add a frontend helper mirroring backend behavior to `frontend/src/lib/permissions.ts`:

```ts
  static canEditTask(member: TeamMember, task: Task): boolean {
    if (this.isModerator(member)) return true;
    return task.assignee_id === member.id || task.created_by_id === member.id;
  }
```

- [ ] **Step 4: Add save handler for detail labels**

In `TaskDetailPage`:

```ts
  async function handleLabelsChange(nextLabels: TaskLabel[]) {
    if (!shortId || !canEditLabels || savingLabels) return;
    const previousLabels = labelDraft;
    setLabelDraft(nextLabels);
    setSavingLabels(true);
    try {
      await api.updateTask(shortId, {
        label_ids: nextLabels.map((label) => label.id),
      });
      await refetch();
      toastSuccess("Метки обновлены");
    } catch {
      setLabelDraft(previousLabels);
      toastError("Не удалось обновить метки");
    } finally {
      setSavingLabels(false);
    }
  }
```

- [ ] **Step 5: Render labels in task detail**

In the badges row, after priority/source badges and before overdue/reminder:

```tsx
          {canEditLabels ? (
            <div className="min-w-[180px] max-w-full">
              <TaskLabelPicker
                value={labelDraft}
                onChange={(nextLabels) => void handleLabelsChange(nextLabels)}
                disabled={savingLabels}
                placeholder="Добавить метки"
              />
            </div>
          ) : (
            <TaskLabelChips labels={task.labels || []} maxVisible={4} />
          )}
```

- [ ] **Step 6: Run frontend verification**

Run:

```bash
cd frontend
npx tsc --noEmit
```

Expected: PASS.

- [ ] **Step 7: Commit task form/detail label editing**

```bash
git add frontend/src/components/tasks/CreateTaskDialog.tsx frontend/src/app/tasks/[id]/page.tsx frontend/src/lib/permissions.ts
git commit -m "feat: edit task labels in web UI"
```

---

## Task 7: End-to-End Verification and Documentation Journal

**Files:**

- Create or modify: `docs/STATUS.md`
- Create or modify: `docs/TEST_PLAN.md`
- Verify: backend and frontend commands below

- [ ] **Step 1: Record status before final verification**

Create or update `docs/STATUS.md`:

```markdown
# Status

## Task Labels

- Current phase: implementation verification
- Spec: `docs/superpowers/specs/2026-05-05-task-labels-design.md`
- Plan: `docs/PLAN.md`
- Scope: web portal task labels only
- Out of scope: Telegram labels, label analytics, personal labels, moderator cleanup UI
```

- [ ] **Step 2: Record test plan**

Create or update `docs/TEST_PLAN.md`:

```markdown
# Test Plan

## Task Labels

### Automated

- `cd backend && pytest tests/test_task_label_repository.py tests/test_task_label_api.py tests/test_task_label_task_api.py tests/test_task_permission_service.py tests/test_task_update_permissions.py -q`
- `cd frontend && npx tsc --noEmit`

### Manual

1. Open the Tasks page.
2. Create a label named `Conference` while creating a task.
3. Add `Conference` and `Partners` to one task.
4. Create another task with no labels.
5. Filter the task board by `Conference`.
6. Confirm the unlabeled task is hidden only while the filter is active.
7. Log in as a user with narrower department access.
8. Confirm the user does not see hidden tasks even when those tasks have matching labels.
```

- [ ] **Step 3: Run backend focused suite**

Run:

```bash
cd backend
pytest tests/test_task_label_repository.py tests/test_task_label_api.py tests/test_task_label_task_api.py tests/test_task_permission_service.py tests/test_task_update_permissions.py -q
```

Expected: PASS.

- [ ] **Step 4: Run backend regression suite**

Run:

```bash
cd backend
pytest -q
```

Expected: PASS.

- [ ] **Step 5: Run frontend typecheck**

Run:

```bash
cd frontend
npx tsc --noEmit
```

Expected: PASS.

- [ ] **Step 6: Run frontend app manually**

Run:

```bash
cd frontend
npm run dev
```

Expected: dev server starts and prints a local URL.

Manual checks:

- Tasks page loads.
- Label filter opens and searches.
- Create task dialog can create/select labels.
- Cards show up to two labels and a `+N` overflow chip.
- Task detail can edit labels.

- [ ] **Step 7: Commit verification docs**

```bash
git add docs/STATUS.md docs/TEST_PLAN.md
git commit -m "docs: add task labels verification plan"
```

---

## Final Implementation Checklist

- [ ] Alembic migration is present and uses revision `029` after `028`.
- [ ] `TaskResponse` includes `labels`.
- [ ] `GET /api/task-labels` returns active labels with usage counts.
- [ ] `POST /api/task-labels` creates labels, deduplicates active slugs, and reactivates archived slugs.
- [ ] `GET /api/tasks?label_ids=...` applies `match=any` label filtering after visibility scope.
- [ ] `POST /api/tasks` and `PATCH /api/tasks/{short_id}` support `label_ids`.
- [ ] Users without task edit permission cannot change labels.
- [ ] Unlabeled tasks remain valid and visually normal.
- [ ] Telegram code paths remain unchanged because all new fields default to empty or `None`.
- [ ] Focused backend tests pass.
- [ ] Frontend typecheck passes.
