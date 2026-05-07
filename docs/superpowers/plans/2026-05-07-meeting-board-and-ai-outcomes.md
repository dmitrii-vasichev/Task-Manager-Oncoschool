# Meeting Board and AI Outcomes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a shareable meeting board for live task-based calls and a manual post-meeting AI outcome review flow from Zoom audio.

**Architecture:** Add two meeting-owned backend records: one for board settings and one for the current AI processing draft. The board API computes live task sections from existing task data and visibility rules; the AI API manually downloads Zoom audio to a temporary file, transcribes it with OpenAI, stores only text/draft metadata, and creates tasks only after moderator confirmation. Frontend adds a `/meetings/[id]/board` route plus meeting-detail entry points and review controls.

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic/PostgreSQL JSONB and ARRAY fields, existing task visibility services, OpenAI Audio Transcriptions API, Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/Radix primitives, lucide-react, Python `pytest`, frontend Node tests, TypeScript, ESLint, Next build.

---

## Source Documents

- Approved design spec: `docs/superpowers/specs/2026-05-07-meeting-board-and-ai-outcomes-design.md`
- Existing meeting API: `backend/app/api/meetings.py`
- Existing meeting service: `backend/app/services/meeting_service.py`
- Existing Zoom service: `backend/app/services/zoom_service.py`
- Existing voice transcription service: `backend/app/services/voice_service.py`
- Existing task API and visibility: `backend/app/api/tasks.py`, `backend/app/services/task_visibility_service.py`
- Existing meeting detail page: `frontend/src/app/meetings/[id]/page.tsx`
- Existing meeting components: `frontend/src/components/meetings/*`
- Existing task card: `frontend/src/components/tasks/TaskCard.tsx`

## Scope Check

This plan covers one cohesive meetings feature with three testable milestones: meeting board, manual audio transcription, and AI outcome draft review. Speaker diarization, automatic recurring-meeting transcription, live AI minutes, and automatic updates to existing tasks remain out of scope.

## File Structure

- Create `backend/alembic/versions/031_meeting_board_ai_outcomes.py`: add `meeting_board_settings` and `meeting_ai_processing`.
- Modify `backend/app/db/models.py`: add `MeetingBoardSettings`, `MeetingAIProcessing`, relationships from `Meeting`.
- Modify `backend/app/db/schemas.py`: add board, material, AI processing, draft, and publish response/request schemas.
- Modify `backend/app/db/repositories.py`: add `MeetingBoardRepository` and `MeetingAIProcessingRepository`.
- Create `backend/app/services/meeting_board_service.py`: compute board scope and visible task sections.
- Create `backend/app/services/meeting_ai_outcomes_service.py`: manage processing state, temporary Zoom audio transcription, draft creation, and publish.
- Modify `backend/app/services/zoom_service.py`: add audio recording selection and temporary download helper.
- Modify `backend/app/services/voice_service.py`: support configurable transcription model and file-path transcription.
- Modify `backend/app/services/ai_service.py`: add a meeting outcome draft parser that returns only summary, decisions, and task candidates.
- Modify `backend/app/api/meetings.py`: add board endpoints, AI processing endpoints, and response models wiring.
- Create `backend/tests/test_meeting_board_service.py`: board section and visibility tests.
- Create `backend/tests/test_meeting_board_api.py`: board API permission and persistence tests.
- Create `backend/tests/test_meeting_ai_outcomes_service.py`: transcription cleanup, status transitions, and publish tests.
- Create `backend/tests/test_meeting_ai_outcomes_api.py`: API permission and no-auto-create tests.
- Modify `frontend/src/lib/types.ts`: add board and AI outcome types.
- Modify `frontend/src/lib/api.ts`: add board and AI outcome client methods.
- Create `frontend/src/components/meetings/meetingBoardUtils.ts`: pure board grouping/status helpers for UI tests.
- Create `frontend/src/components/meetings/meetingBoardUtils.test.ts`: frontend unit tests for section labels and task grouping helpers.
- Create `frontend/src/app/meetings/[id]/board/page.tsx`: shareable meeting board route.
- Create `frontend/src/components/meetings/MeetingBoardHeader.tsx`: compact screen-share header.
- Create `frontend/src/components/meetings/MeetingBoardSection.tsx`: section renderer for task cards.
- Create `frontend/src/components/meetings/MeetingBoardScopePanel.tsx`: moderator-only context controls.
- Create `frontend/src/components/meetings/MeetingBoardMaterials.tsx`: links and board notes editor/display.
- Create `frontend/src/components/meetings/MeetingAiOutcomesPanel.tsx`: manual transcription and review panel on meeting detail.
- Modify `frontend/src/app/meetings/[id]/page.tsx`: add board entry point and AI outcomes panel.
- Modify `frontend/package.json`: include `meetingBoardUtils.test.ts` in `npm test`.
- Modify `docs/PLAN.md`: link this implementation plan as the active plan.
- Modify `docs/STATUS.md`: record planning state.
- Modify `docs/TEST_PLAN.md`: add board and AI outcomes validation.

## Task 1: Backend Data Model and Schemas

**Files:**

- Create: `backend/alembic/versions/031_meeting_board_ai_outcomes.py`
- Modify: `backend/app/db/models.py`
- Modify: `backend/app/db/schemas.py`
- Create: `backend/tests/test_meeting_ai_outcomes_service.py`

- [ ] **Step 1: Add schema/model smoke tests**

Create `backend/tests/test_meeting_ai_outcomes_service.py` with the initial schema tests:

```python
import uuid

from app.db.schemas import (
    MeetingAIProcessingResponse,
    MeetingBoardSettingsResponse,
    MeetingBoardTaskDraft,
)


def test_board_settings_response_defaults_are_empty() -> None:
    response = MeetingBoardSettingsResponse(
        id=uuid.uuid4(),
        meeting_id=uuid.uuid4(),
        added_member_ids=[],
        added_department_ids=[],
        pinned_task_ids=[],
        materials=[],
        board_notes=None,
        created_by_id=None,
        updated_by_id=None,
        created_at=None,
        updated_at=None,
    )

    assert response.added_member_ids == []
    assert response.materials == []


def test_ai_processing_response_supports_openai_audio_source() -> None:
    response = MeetingAIProcessingResponse(
        id=uuid.uuid4(),
        meeting_id=uuid.uuid4(),
        status="draft_ready",
        transcript_source="openai_audio",
        transcription_model="gpt-4o-mini-transcribe",
        started_at=None,
        completed_at=None,
        error_message=None,
        transcript_char_count=123,
        audio_duration_seconds=None,
        estimated_cost_usd=None,
        draft_summary="Summary",
        draft_decisions=["Decision"],
        draft_tasks=[
            MeetingBoardTaskDraft(
                title="Prepare deck",
                description=None,
                assignee_name=None,
                assignee_id=None,
                deadline=None,
                priority="normal",
                selected=True,
            )
        ],
        published_at=None,
        published_by_id=None,
    )

    assert response.transcript_source == "openai_audio"
    assert response.draft_tasks[0].selected is True
```

- [ ] **Step 2: Run schema tests to verify failure**

Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest tests/test_meeting_ai_outcomes_service.py -q
```

Expected: fails because the new schemas do not exist.

- [ ] **Step 3: Add SQLAlchemy models**

In `backend/app/db/models.py`, add the models after `MeetingParticipant`:

```python
class MeetingBoardSettings(Base):
    __tablename__ = "meeting_board_settings"
    __table_args__ = (
        UniqueConstraint("meeting_id", name="uq_meeting_board_settings_meeting_id"),
        Index("idx_meeting_board_settings_meeting_id", "meeting_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False
    )
    added_member_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), default=list, server_default="{}"
    )
    added_department_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), default=list, server_default="{}"
    )
    pinned_task_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), default=list, server_default="{}"
    )
    materials: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, server_default="[]", nullable=False
    )
    board_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("team_members.id", ondelete="SET NULL"), nullable=True
    )
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("team_members.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    meeting: Mapped["Meeting"] = relationship(back_populates="board_settings")


class MeetingAIProcessing(Base):
    __tablename__ = "meeting_ai_processing"
    __table_args__ = (
        UniqueConstraint("meeting_id", name="uq_meeting_ai_processing_meeting_id"),
        Index("idx_meeting_ai_processing_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(40), default="idle", server_default="idle", nullable=False
    )
    transcript_source: Mapped[str | None] = mapped_column(String(40), nullable=True)
    transcription_model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_char_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    audio_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    draft_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    draft_decisions: Mapped[list[str]] = mapped_column(
        JSONB, default=list, server_default="[]", nullable=False
    )
    draft_tasks: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, server_default="[]", nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    published_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("team_members.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    meeting: Mapped["Meeting"] = relationship(back_populates="ai_processing")
```

Add relationships to `Meeting`:

```python
board_settings: Mapped["MeetingBoardSettings | None"] = relationship(
    back_populates="meeting", cascade="all, delete-orphan", uselist=False
)
ai_processing: Mapped["MeetingAIProcessing | None"] = relationship(
    back_populates="meeting", cascade="all, delete-orphan", uselist=False
)
```

- [ ] **Step 4: Add Alembic migration**

Create `backend/alembic/versions/031_meeting_board_ai_outcomes.py`:

```python
"""meeting board and ai outcomes

Revision ID: 031_meeting_board_ai_outcomes
Revises: 030_task_urgency_binary
Create Date: 2026-05-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "031_meeting_board_ai_outcomes"
down_revision: Union[str, None] = "030_task_urgency_binary"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "meeting_board_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("meeting_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("added_member_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default="{}", nullable=False),
        sa.Column("added_department_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default="{}", nullable=False),
        sa.Column("pinned_task_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default="{}", nullable=False),
        sa.Column("materials", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("board_notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["team_members.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["team_members.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("meeting_id", name="uq_meeting_board_settings_meeting_id"),
    )
    op.create_index("idx_meeting_board_settings_meeting_id", "meeting_board_settings", ["meeting_id"])

    op.create_table(
        "meeting_ai_processing",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("meeting_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="idle", nullable=False),
        sa.Column("transcript_source", sa.String(length=40), nullable=True),
        sa.Column("transcription_model", sa.String(length=80), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("transcript_char_count", sa.Integer(), nullable=True),
        sa.Column("audio_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("estimated_cost_usd", sa.Numeric(10, 4), nullable=True),
        sa.Column("draft_summary", sa.Text(), nullable=True),
        sa.Column("draft_decisions", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("draft_tasks", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("published_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["published_by_id"], ["team_members.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("meeting_id", name="uq_meeting_ai_processing_meeting_id"),
    )
    op.create_index("idx_meeting_ai_processing_status", "meeting_ai_processing", ["status"])


def downgrade() -> None:
    op.drop_index("idx_meeting_ai_processing_status", table_name="meeting_ai_processing")
    op.drop_table("meeting_ai_processing")
    op.drop_index("idx_meeting_board_settings_meeting_id", table_name="meeting_board_settings")
    op.drop_table("meeting_board_settings")
```

- [ ] **Step 5: Add Pydantic schemas**

In `backend/app/db/schemas.py`, add:

```python
MeetingAIProcessingStatusType = Literal[
    "idle", "recording_not_ready", "recording_ready", "transcribing",
    "transcript_ready", "draft_ready", "published", "failed"
]
MeetingTranscriptSourceType = Literal["manual", "zoom_api", "openai_audio"]
```

Add schemas near meeting schemas:

```python
class MeetingBoardMaterial(BaseModel):
    id: str
    title: str
    url: str
    description: str | None = None


class MeetingBoardSettingsUpdate(BaseModel):
    added_member_ids: list[uuid.UUID] | None = None
    added_department_ids: list[uuid.UUID] | None = None
    pinned_task_ids: list[uuid.UUID] | None = None
    materials: list[MeetingBoardMaterial] | None = None
    board_notes: str | None = None


class MeetingBoardSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    meeting_id: uuid.UUID
    added_member_ids: list[uuid.UUID] = Field(default_factory=list)
    added_department_ids: list[uuid.UUID] = Field(default_factory=list)
    pinned_task_ids: list[uuid.UUID] = Field(default_factory=list)
    materials: list[MeetingBoardMaterial] = Field(default_factory=list)
    board_notes: str | None = None
    created_by_id: uuid.UUID | None = None
    updated_by_id: uuid.UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MeetingBoardResponse(BaseModel):
    meeting: MeetingResponse
    settings: MeetingBoardSettingsResponse
    urgent: list[TaskResponse] = Field(default_factory=list)
    in_progress: list[TaskResponse] = Field(default_factory=list)
    review: list[TaskResponse] = Field(default_factory=list)
    done_this_week: list[TaskResponse] = Field(default_factory=list)


class MeetingBoardTaskDraft(BaseModel):
    title: str
    description: str | None = None
    assignee_name: str | None = None
    assignee_id: uuid.UUID | None = None
    deadline: date | None = None
    priority: TaskPriorityType = "normal"
    selected: bool = True


class MeetingAIProcessingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    meeting_id: uuid.UUID
    status: MeetingAIProcessingStatusType
    transcript_source: MeetingTranscriptSourceType | None = None
    transcription_model: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    transcript_char_count: int | None = None
    audio_duration_seconds: int | None = None
    estimated_cost_usd: Decimal | None = None
    draft_summary: str | None = None
    draft_decisions: list[str] = Field(default_factory=list)
    draft_tasks: list[MeetingBoardTaskDraft] = Field(default_factory=list)
    published_at: datetime | None = None
    published_by_id: uuid.UUID | None = None


class MeetingAIProcessingDraftUpdate(BaseModel):
    draft_summary: str
    draft_decisions: list[str] = Field(default_factory=list)
    draft_tasks: list[MeetingBoardTaskDraft] = Field(default_factory=list)


class MeetingAIPublishRequest(BaseModel):
    draft_summary: str
    draft_decisions: list[str] = Field(default_factory=list)
    draft_tasks: list[MeetingBoardTaskDraft] = Field(default_factory=list)
```

Add `Decimal` to imports:

```python
from decimal import Decimal
```

- [ ] **Step 6: Run schema tests**

Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest tests/test_meeting_ai_outcomes_service.py -q
```

Expected: passes.

- [ ] **Step 7: Commit**

```bash
git add backend/alembic/versions/031_meeting_board_ai_outcomes.py backend/app/db/models.py backend/app/db/schemas.py backend/tests/test_meeting_ai_outcomes_service.py
git commit -m "feat: add meeting board outcome data model"
```

## Task 2: Board Repositories, Service, and API

**Files:**

- Modify: `backend/app/db/repositories.py`
- Create: `backend/app/services/meeting_board_service.py`
- Modify: `backend/app/api/meetings.py`
- Create: `backend/tests/test_meeting_board_service.py`
- Create: `backend/tests/test_meeting_board_api.py`

- [ ] **Step 1: Add failing board service tests**

Create `backend/tests/test_meeting_board_service.py`:

```python
import uuid
from datetime import date, datetime, timedelta
from types import SimpleNamespace

from app.services.meeting_board_service import group_board_tasks


def task(**overrides):
    base = {
        "id": uuid.uuid4(),
        "short_id": 1,
        "status": "new",
        "priority": "normal",
        "deadline": None,
        "completed_at": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_group_board_tasks_keeps_overdue_inside_work_section() -> None:
    old_deadline = date.today() - timedelta(days=1)
    grouped = group_board_tasks(
        [
            task(short_id=10, status="in_progress", deadline=old_deadline),
            task(short_id=11, status="review", deadline=old_deadline),
        ],
        today=date.today(),
    )

    assert [t.short_id for t in grouped.in_progress] == [10]
    assert [t.short_id for t in grouped.review] == [11]
    assert grouped.urgent == []


def test_group_board_tasks_includes_done_this_week_only() -> None:
    now = datetime.utcnow()
    grouped = group_board_tasks(
        [
            task(short_id=20, status="done", completed_at=now - timedelta(days=2)),
            task(short_id=21, status="done", completed_at=now - timedelta(days=9)),
        ],
        today=date.today(),
        now=now,
    )

    assert [t.short_id for t in grouped.done_this_week] == [20]
```

- [ ] **Step 2: Run board service tests to verify failure**

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest tests/test_meeting_board_service.py -q
```

Expected: fails because `meeting_board_service.py` does not exist.

- [ ] **Step 3: Add repositories**

In `backend/app/db/repositories.py`, import the new models and add:

```python
class MeetingBoardRepository:
    async def get_by_meeting_id(self, session: AsyncSession, meeting_id: uuid.UUID) -> MeetingBoardSettings | None:
        result = await session.execute(
            select(MeetingBoardSettings).where(MeetingBoardSettings.meeting_id == meeting_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        session: AsyncSession,
        meeting_id: uuid.UUID,
        member: TeamMember | None = None,
    ) -> MeetingBoardSettings:
        existing = await self.get_by_meeting_id(session, meeting_id)
        if existing:
            return existing
        settings = MeetingBoardSettings(
            meeting_id=meeting_id,
            created_by_id=getattr(member, "id", None),
            updated_by_id=getattr(member, "id", None),
        )
        session.add(settings)
        await session.flush()
        return settings

    async def update(
        self,
        session: AsyncSession,
        settings: MeetingBoardSettings,
        *,
        member: TeamMember,
        **fields,
    ) -> MeetingBoardSettings:
        for key, value in fields.items():
            setattr(settings, key, value)
        settings.updated_by_id = member.id
        await session.flush()
        return settings
```

- [ ] **Step 4: Add board service**

Create `backend/app/services/meeting_board_service.py`:

```python
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Meeting, Task, TeamMember
from app.db.repositories import MeetingBoardRepository
from app.services.task_visibility_service import can_access_task, resolve_visible_department_ids


@dataclass
class BoardTaskGroups:
    urgent: list[Task] = field(default_factory=list)
    in_progress: list[Task] = field(default_factory=list)
    review: list[Task] = field(default_factory=list)
    done_this_week: list[Task] = field(default_factory=list)


def group_board_tasks(
    tasks: list[Task],
    *,
    today: date | None = None,
    now: datetime | None = None,
) -> BoardTaskGroups:
    today = today or date.today()
    now = now or datetime.utcnow()
    done_cutoff = now - timedelta(days=7)
    groups = BoardTaskGroups()
    seen: set[uuid.UUID] = set()

    for task in sorted(tasks, key=lambda item: getattr(item, "short_id", 0)):
        if task.id in seen:
            continue
        seen.add(task.id)
        if task.status == "done":
            completed_at = getattr(task, "completed_at", None)
            if completed_at and completed_at >= done_cutoff:
                groups.done_this_week.append(task)
            continue
        if task.priority == "urgent":
            groups.urgent.append(task)
            continue
        if task.status == "in_progress":
            groups.in_progress.append(task)
            continue
        if task.status == "review":
            groups.review.append(task)
    return groups


class MeetingBoardService:
    def __init__(self) -> None:
        self.board_repo = MeetingBoardRepository()

    async def get_board(self, session: AsyncSession, meeting: Meeting, viewer: TeamMember) -> tuple:
        settings = await self.board_repo.get_or_create(session, meeting.id, viewer)
        tasks = await self._load_visible_tasks(session, meeting, settings, viewer)
        groups = group_board_tasks(tasks)
        return settings, groups

    async def _load_visible_tasks(self, session: AsyncSession, meeting: Meeting, settings, viewer: TeamMember) -> list[Task]:
        participant_ids = [participant.member_id for participant in (meeting.participants or [])]
        member_ids = list(dict.fromkeys([*participant_ids, *(settings.added_member_ids or [])]))
        department_ids = list(settings.added_department_ids or [])
        pinned_ids = list(settings.pinned_task_ids or [])

        visible_department_ids = await resolve_visible_department_ids(session, viewer)

        stmt = select(Task).options(
            selectinload(Task.assignee),
            selectinload(Task.created_by),
            selectinload(Task.labels),
        )

        filters = []
        if member_ids:
            filters.append(Task.assignee_id.in_(member_ids))
        if department_ids:
            filters.append(Task.assignee.has(TeamMember.department_id.in_(department_ids)))
        if pinned_ids:
            filters.append(Task.id.in_(pinned_ids))
        if not filters:
            return []
        stmt = stmt.where(or_(*filters))

        if visible_department_ids is not None:
            if visible_department_ids:
                stmt = stmt.where(Task.assignee.has(TeamMember.department_id.in_(visible_department_ids)))
            else:
                stmt = stmt.where(Task.assignee_id == viewer.id)

        result = await session.execute(stmt)
        tasks = list(result.scalars().unique().all())
        visible_tasks = []
        for task in tasks:
            if await can_access_task(session, viewer, task):
                visible_tasks.append(task)
        return visible_tasks
```

- [ ] **Step 5: Run board service tests**

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest tests/test_meeting_board_service.py -q
```

Expected: passes.

- [ ] **Step 6: Add board API tests**

Create `backend/tests/test_meeting_board_api.py`:

```python
import uuid
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.api import meetings as meetings_api
from app.db.schemas import MeetingBoardSettingsUpdate


class MeetingBoardApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_update_board_requires_moderator(self) -> None:
        member = SimpleNamespace(id=uuid.uuid4(), role="member")
        session = SimpleNamespace()

        with self.assertRaises(meetings_api.HTTPException) as ctx:
            await meetings_api.update_meeting_board_settings(
                meeting_id=uuid.uuid4(),
                data=MeetingBoardSettingsUpdate(board_notes="Notes"),
                member=member,
                session=session,
            )

        self.assertEqual(ctx.exception.status_code, 403)

    async def test_get_board_returns_service_response(self) -> None:
        meeting_id = uuid.uuid4()
        member = SimpleNamespace(id=uuid.uuid4(), role="member")
        meeting = SimpleNamespace(id=meeting_id, participants=[], status="scheduled")
        settings = SimpleNamespace(
            id=uuid.uuid4(),
            meeting_id=meeting_id,
            added_member_ids=[],
            added_department_ids=[],
            pinned_task_ids=[],
            materials=[],
            board_notes=None,
            created_by_id=None,
            updated_by_id=None,
            created_at=None,
            updated_at=None,
        )
        groups = SimpleNamespace(urgent=[], in_progress=[], review=[], done_this_week=[])
        session = SimpleNamespace()

        with patch.object(meetings_api.meeting_service, "get_meeting_by_id", AsyncMock(return_value=meeting)), \
             patch.object(meetings_api.meeting_board_service, "get_board", AsyncMock(return_value=(settings, groups))):
            response = await meetings_api.get_meeting_board(
                meeting_id=meeting_id,
                member=member,
                session=session,
            )

        self.assertEqual(response.settings.meeting_id, meeting_id)
        self.assertEqual(response.urgent, [])
```

- [ ] **Step 7: Add board endpoints**

In `backend/app/api/meetings.py`, import schemas and service:

```python
from app.db.schemas import (
    MeetingBoardResponse,
    MeetingBoardSettingsResponse,
    MeetingBoardSettingsUpdate,
    MeetingResponse,
    TaskResponse,
)
from app.services.meeting_board_service import MeetingBoardService

meeting_board_service = MeetingBoardService()
```

Add endpoints before transcript endpoints:

```python
@router.get("/{meeting_id}/board", response_model=MeetingBoardResponse)
async def get_meeting_board(
    meeting_id: uuid.UUID,
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    meeting = await meeting_service.get_meeting_by_id(session, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Встреча не найдена")
    settings, groups = await meeting_board_service.get_board(session, meeting, member)
    return MeetingBoardResponse(
        meeting=_meeting_response(meeting),
        settings=MeetingBoardSettingsResponse.model_validate(settings),
        urgent=groups.urgent,
        in_progress=groups.in_progress,
        review=groups.review,
        done_this_week=groups.done_this_week,
    )


@router.patch("/{meeting_id}/board/settings", response_model=MeetingBoardSettingsResponse)
async def update_meeting_board_settings(
    meeting_id: uuid.UUID,
    data: MeetingBoardSettingsUpdate,
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not PermissionService.is_moderator(member):
        raise HTTPException(status_code=403, detail="Только модератор может менять доску встречи")
    meeting = await meeting_service.get_meeting_by_id(session, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Встреча не найдена")
    settings = await meeting_board_service.board_repo.get_or_create(session, meeting_id, member)
    fields = data.model_dump(exclude_unset=True)
    updated = await meeting_board_service.board_repo.update(
        session, settings, member=member, **fields
    )
    await session.commit()
    return MeetingBoardSettingsResponse.model_validate(updated)
```

- [ ] **Step 8: Run board API tests**

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest tests/test_meeting_board_service.py tests/test_meeting_board_api.py -q
```

Expected: passes.

- [ ] **Step 9: Commit**

```bash
git add backend/app/db/repositories.py backend/app/services/meeting_board_service.py backend/app/api/meetings.py backend/tests/test_meeting_board_service.py backend/tests/test_meeting_board_api.py
git commit -m "feat: add meeting board API"
```

## Task 3: Manual Zoom Audio Transcription

**Files:**

- Modify: `backend/app/services/zoom_service.py`
- Modify: `backend/app/services/voice_service.py`
- Create: `backend/app/services/meeting_ai_outcomes_service.py`
- Modify: `backend/app/api/meetings.py`
- Modify: `backend/tests/test_meeting_ai_outcomes_service.py`
- Create: `backend/tests/test_meeting_ai_outcomes_api.py`

- [ ] **Step 1: Add failing temporary cleanup test**

Append to `backend/tests/test_meeting_ai_outcomes_service.py`:

```python
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.services.meeting_ai_outcomes_service import MeetingAIOutcomesService


class MeetingAIOutcomesServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_transcribe_audio_deletes_temporary_file_on_failure(self) -> None:
        service = MeetingAIOutcomesService()
        fd, path = tempfile.mkstemp(suffix=".m4a")
        os.close(fd)
        with open(path, "wb") as fh:
            fh.write(b"audio")

        zoom_service = SimpleNamespace(
            download_audio_recording=AsyncMock(return_value=path)
        )
        voice_service = SimpleNamespace(
            transcribe_file=AsyncMock(side_effect=RuntimeError("openai down"))
        )

        with self.assertRaises(RuntimeError):
            await service._transcribe_temp_audio(
                zoom_service=zoom_service,
                voice_service=voice_service,
                zoom_meeting_id="123",
                model="gpt-4o-mini-transcribe",
            )

        self.assertFalse(os.path.exists(path))
```

- [ ] **Step 2: Run AI service test to verify failure**

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest tests/test_meeting_ai_outcomes_service.py::MeetingAIOutcomesServiceTests::test_transcribe_audio_deletes_temporary_file_on_failure -q
```

Expected: fails because `meeting_ai_outcomes_service.py` does not exist.

- [ ] **Step 3: Extend Zoom service**

In `backend/app/services/zoom_service.py`, add:

```python
    def _select_audio_recording_file(self, recordings: dict | None) -> dict | None:
        if not recordings or "recording_files" not in recordings:
            return None
        files = recordings["recording_files"]
        preferred = ["M4A", "MP4"]
        for file_type in preferred:
            match = next(
                (
                    f for f in files
                    if f.get("file_type") == file_type and f.get("download_url")
                ),
                None,
            )
            if match:
                return match
        return None

    async def download_audio_recording(self, meeting_id: str) -> str | None:
        recordings = await self.get_recordings(meeting_id)
        audio_file = self._select_audio_recording_file(recordings)
        if not audio_file:
            return None

        suffix = ".m4a" if audio_file.get("file_type") == "M4A" else ".mp4"
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_path = temp.name
        temp.close()

        token = await self._get_token()
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "GET",
                    audio_file["download_url"],
                    headers={"Authorization": f"Bearer {token}"},
                    follow_redirects=True,
                ) as resp:
                    resp.raise_for_status()
                    with open(temp_path, "wb") as fh:
                        async for chunk in resp.aiter_bytes():
                            fh.write(chunk)
            return temp_path
        except Exception:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass
            raise
```

Add imports:

```python
import os
import tempfile
```

- [ ] **Step 4: Extend VoiceService**

In `backend/app/services/voice_service.py`, add constants and method:

```python
DEFAULT_TRANSCRIPTION_MODEL = "gpt-4o-mini-transcribe"
OPENAI_TRANSCRIPTION_MAX_BYTES = 25 * 1024 * 1024


    async def transcribe_file(
        self,
        file_path: str,
        *,
        model: str = DEFAULT_TRANSCRIPTION_MODEL,
        language: str = "ru",
    ) -> str:
        size = os.path.getsize(file_path)
        if size > OPENAI_TRANSCRIPTION_MAX_BYTES:
            raise ValueError("Аудиофайл больше 25 МБ. Для этой записи пока нужна ручная обработка или сжатие.")
        with open(file_path, "rb") as audio_file:
            transcript = await self.client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                language=language,
                response_format="text",
            )
        return transcript if isinstance(transcript, str) else transcript.text
```

Add `import os`.

Update `transcribe()` to use the new default model only if desired for Telegram voice:

```python
transcript = await self.client.audio.transcriptions.create(
    model=DEFAULT_TRANSCRIPTION_MODEL,
    file=audio_file,
    language="ru",
)
```

- [ ] **Step 5: Add AI outcomes service transcription method**

Create `backend/app/services/meeting_ai_outcomes_service.py`:

```python
import os
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Meeting, MeetingAIProcessing, TeamMember
from app.db.repositories import MeetingAIProcessingRepository
from app.services.voice_service import DEFAULT_TRANSCRIPTION_MODEL, VoiceService


class MeetingAIOutcomesService:
    def __init__(self) -> None:
        self.processing_repo = MeetingAIProcessingRepository()
        self.voice_service = VoiceService()

    async def _transcribe_temp_audio(self, *, zoom_service, voice_service, zoom_meeting_id: str, model: str) -> str:
        temp_path = await zoom_service.download_audio_recording(zoom_meeting_id)
        if not temp_path:
            raise ValueError("Аудиозапись встречи недоступна в Zoom")
        try:
            return await voice_service.transcribe_file(temp_path, model=model, language="ru")
        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    async def transcribe_meeting_audio(
        self,
        session: AsyncSession,
        *,
        meeting: Meeting,
        zoom_service,
        moderator: TeamMember,
        model: str = DEFAULT_TRANSCRIPTION_MODEL,
    ) -> MeetingAIProcessing:
        if not meeting.zoom_meeting_id or not zoom_service:
            raise ValueError("Zoom-запись недоступна")

        processing = await self.processing_repo.get_or_create(session, meeting.id)
        processing.status = "transcribing"
        processing.started_at = datetime.utcnow()
        processing.completed_at = None
        processing.error_message = None
        processing.transcription_model = model
        await session.flush()

        try:
            transcript = await self._transcribe_temp_audio(
                zoom_service=zoom_service,
                voice_service=self.voice_service,
                zoom_meeting_id=meeting.zoom_meeting_id,
                model=model,
            )
        except Exception as exc:
            processing.status = "failed"
            processing.error_message = str(exc)
            processing.completed_at = datetime.utcnow()
            await session.flush()
            raise

        meeting.transcript = transcript
        meeting.transcript_source = "openai_audio"
        processing.status = "transcript_ready"
        processing.transcript_source = "openai_audio"
        processing.transcript_char_count = len(transcript)
        processing.completed_at = datetime.utcnow()
        await session.flush()
        return processing
```

- [ ] **Step 6: Add processing repository**

In `backend/app/db/repositories.py`, add:

```python
class MeetingAIProcessingRepository:
    async def get_by_meeting_id(self, session: AsyncSession, meeting_id: uuid.UUID) -> MeetingAIProcessing | None:
        result = await session.execute(
            select(MeetingAIProcessing).where(MeetingAIProcessing.meeting_id == meeting_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, session: AsyncSession, meeting_id: uuid.UUID) -> MeetingAIProcessing:
        existing = await self.get_by_meeting_id(session, meeting_id)
        if existing:
            return existing
        processing = MeetingAIProcessing(meeting_id=meeting_id, status="idle")
        session.add(processing)
        await session.flush()
        return processing
```

- [ ] **Step 7: Add transcribe endpoint**

In `backend/app/api/meetings.py`, instantiate:

```python
from app.db.schemas import MeetingAIProcessingResponse
from app.services.meeting_ai_outcomes_service import MeetingAIOutcomesService

meeting_ai_outcomes_service = MeetingAIOutcomesService()
```

Add endpoint:

```python
@router.post("/{meeting_id}/ai/transcribe-audio", response_model=MeetingAIProcessingResponse)
async def transcribe_meeting_audio(
    meeting_id: uuid.UUID,
    request: Request,
    member: TeamMember = Depends(require_moderator),
    session: AsyncSession = Depends(get_session),
):
    meeting = await meeting_service.get_meeting_by_id(session, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Встреча не найдена")
    try:
        processing = await meeting_ai_outcomes_service.transcribe_meeting_audio(
            session,
            meeting=meeting,
            zoom_service=_get_zoom_service(request),
            moderator=member,
        )
        await session.commit()
        return MeetingAIProcessingResponse.model_validate(processing)
    except ValueError as exc:
        await session.commit()
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        await session.commit()
        logger.exception("Audio transcription failed for meeting %s", meeting_id)
        raise HTTPException(status_code=502, detail=f"Ошибка транскрибации: {exc}")
```

- [ ] **Step 8: Add endpoint API tests**

Create `backend/tests/test_meeting_ai_outcomes_api.py`:

```python
import uuid
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.api import meetings as meetings_api


class MeetingAIOutcomesApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_transcribe_audio_requires_moderator_dependency_contract(self) -> None:
        meeting_id = uuid.uuid4()
        member = SimpleNamespace(id=uuid.uuid4(), role="moderator")
        meeting = SimpleNamespace(id=meeting_id, zoom_meeting_id="123")
        processing = SimpleNamespace(
            id=uuid.uuid4(),
            meeting_id=meeting_id,
            status="transcript_ready",
            transcript_source="openai_audio",
            transcription_model="gpt-4o-mini-transcribe",
            started_at=None,
            completed_at=None,
            error_message=None,
            transcript_char_count=50,
            audio_duration_seconds=None,
            estimated_cost_usd=None,
            draft_summary=None,
            draft_decisions=[],
            draft_tasks=[],
            published_at=None,
            published_by_id=None,
        )
        session = SimpleNamespace(commit=AsyncMock())
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(zoom_service=SimpleNamespace())))

        with patch.object(meetings_api.meeting_service, "get_meeting_by_id", AsyncMock(return_value=meeting)), \
             patch.object(meetings_api.meeting_ai_outcomes_service, "transcribe_meeting_audio", AsyncMock(return_value=processing)):
            response = await meetings_api.transcribe_meeting_audio(
                meeting_id=meeting_id,
                request=request,
                member=member,
                session=session,
            )

        self.assertEqual(response.status, "transcript_ready")
        session.commit.assert_awaited_once()
```

- [ ] **Step 9: Run transcription tests**

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest tests/test_meeting_ai_outcomes_service.py tests/test_meeting_ai_outcomes_api.py -q
```

Expected: passes.

- [ ] **Step 10: Commit**

```bash
git add backend/app/services/zoom_service.py backend/app/services/voice_service.py backend/app/services/meeting_ai_outcomes_service.py backend/app/db/repositories.py backend/app/api/meetings.py backend/tests/test_meeting_ai_outcomes_service.py backend/tests/test_meeting_ai_outcomes_api.py
git commit -m "feat: add manual meeting audio transcription"
```

## Task 4: AI Draft Generation and Publishing

**Files:**

- Modify: `backend/app/services/ai_service.py`
- Modify: `backend/app/services/meeting_ai_outcomes_service.py`
- Modify: `backend/app/api/meetings.py`
- Modify: `backend/tests/test_meeting_ai_outcomes_service.py`
- Modify: `backend/tests/test_meeting_ai_outcomes_api.py`

- [ ] **Step 1: Add failing publish test**

Append to `backend/tests/test_meeting_ai_outcomes_service.py`:

```python
    async def test_publish_creates_only_selected_task_candidates(self) -> None:
        service = MeetingAIOutcomesService()
        meeting = SimpleNamespace(id=uuid.uuid4(), parsed_summary=None, decisions=[], status="scheduled")
        moderator = SimpleNamespace(id=uuid.uuid4(), role="moderator")
        created = SimpleNamespace(id=uuid.uuid4())
        service.meeting_service = SimpleNamespace(
            create_tasks_from_parsed=AsyncMock(return_value=[created])
        )
        service.member_repo = SimpleNamespace(get_all_active=AsyncMock(return_value=[]))
        session = SimpleNamespace(flush=AsyncMock())
        processing = SimpleNamespace(
            status="draft_ready",
            draft_summary="Summary",
            draft_decisions=["Decision"],
            draft_tasks=[],
            published_at=None,
            published_by_id=None,
        )

        result = await service.publish_outcomes(
            session,
            meeting=meeting,
            processing=processing,
            moderator=moderator,
            draft_summary="Final summary",
            draft_decisions=["Decision"],
            draft_tasks=[
                {"title": "Selected", "priority": "normal", "selected": True},
                {"title": "Rejected", "priority": "normal", "selected": False},
            ],
        )

        assert result == [created]
        service.meeting_service.create_tasks_from_parsed.assert_awaited_once()
        args = service.meeting_service.create_tasks_from_parsed.await_args.args
        assert args[2] == [{"title": "Selected", "priority": "normal", "selected": True}]
```

- [ ] **Step 2: Run publish test to verify failure**

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest tests/test_meeting_ai_outcomes_service.py::MeetingAIOutcomesServiceTests::test_publish_creates_only_selected_task_candidates -q
```

Expected: fails because `publish_outcomes` does not exist.

- [ ] **Step 3: Add outcome parser prompt**

In `backend/app/services/ai_service.py`, add:

```python
MEETING_OUTCOMES_PROMPT = """Ты — ассистент для подготовки черновика итогов встречи.

Участники команды (JSON):
{team_members_json}

Проанализируй транскрипт встречи. Ответь строго JSON без markdown:

{{
  "summary": "краткое резюме встречи в 5-10 строк",
  "decisions": ["решение 1", "решение 2"],
  "tasks": [
    {{
      "title": "конкретная новая задача",
      "description": "контекст задачи или null",
      "assignee_name": "имя исполнителя из списка или null",
      "priority": "normal | urgent",
      "deadline": "YYYY-MM-DD или null"
    }}
  ]
}}

Правила:
- Не создавай задачи из общих обсуждений.
- Не обновляй существующие задачи, только предлагай новые задачи.
- Если решение не сформулировано явно, не добавляй его.
- Если исполнитель или срок неясны, используй null.
- Сегодня: {today}.
"""
```

Add method:

```python
    async def parse_meeting_outcomes(
        self,
        session: AsyncSession,
        transcript_text: str,
        team_members: list[TeamMember],
    ) -> ParsedMeeting:
        provider = await self._get_current_provider(session, feature_key="meetings_summary")
        team_json = json.dumps(
            [{"name": m.full_name, "variants": m.name_variants or []} for m in team_members],
            ensure_ascii=False,
        )
        system_prompt = MEETING_OUTCOMES_PROMPT.format(
            team_members_json=team_json,
            today=date.today().isoformat(),
        )
        prepared_text = self._prepare_meeting_text(transcript_text)
        chunks = self._split_meeting_text(prepared_text, model_hint=getattr(provider, "model", None))
        parsed_chunks = []
        for chunk in chunks:
            response = await self._complete_with_retry(provider, system_prompt, chunk)
            data = self._extract_json(response)
            parsed_chunks.append(ParsedMeeting(title="", participants=[], **data))
        return self._merge_parsed_chunks(parsed_chunks)
```

- [ ] **Step 4: Add draft and publish service methods**

In `backend/app/services/meeting_ai_outcomes_service.py`, import `AIService`, `MeetingService`, `TeamMemberRepository`, and add:

```python
    async def generate_draft(
        self,
        session: AsyncSession,
        *,
        meeting: Meeting,
    ) -> MeetingAIProcessing:
        if not meeting.transcript:
            raise ValueError("Нет транскрипции для генерации итогов")
        processing = await self.processing_repo.get_or_create(session, meeting.id)
        members = await self.member_repo.get_all_active(session)
        parsed = await self.ai_service.parse_meeting_outcomes(session, meeting.transcript, members)
        processing.status = "draft_ready"
        processing.draft_summary = parsed.summary
        processing.draft_decisions = parsed.decisions
        processing.draft_tasks = [
            {
                "title": task.title,
                "description": task.description,
                "assignee_name": task.assignee_name,
                "assignee_id": None,
                "deadline": task.deadline,
                "priority": normalize_task_urgency(task.priority),
                "selected": True,
            }
            for task in parsed.tasks
        ]
        await session.flush()
        return processing

    async def publish_outcomes(
        self,
        session: AsyncSession,
        *,
        meeting: Meeting,
        processing: MeetingAIProcessing,
        moderator: TeamMember,
        draft_summary: str,
        draft_decisions: list[str],
        draft_tasks: list[dict],
    ) -> list:
        selected_tasks = []
        for task in draft_tasks:
            if not task.get("selected", True):
                continue
            normalized_task = dict(task)
            deadline = normalized_task.get("deadline")
            if hasattr(deadline, "isoformat"):
                normalized_task["deadline"] = deadline.isoformat()
            selected_tasks.append(normalized_task)
        members = await self.member_repo.get_all_active(session)
        meeting.parsed_summary = draft_summary
        meeting.decisions = draft_decisions
        if meeting.status != "completed":
            meeting.status = "completed"
        created_tasks = await self.meeting_service.create_tasks_from_parsed(
            session, meeting, selected_tasks, moderator, members
        )
        processing.status = "published"
        processing.draft_summary = draft_summary
        processing.draft_decisions = draft_decisions
        processing.draft_tasks = draft_tasks
        processing.published_at = datetime.utcnow()
        processing.published_by_id = moderator.id
        await session.flush()
        return created_tasks
```

Initialize dependencies in `__init__`:

```python
self.ai_service = AIService()
self.meeting_service = MeetingService()
self.member_repo = TeamMemberRepository()
```

- [ ] **Step 5: Add draft/publish endpoints**

In `backend/app/api/meetings.py`, add:

```python
@router.post("/{meeting_id}/ai/generate-draft", response_model=MeetingAIProcessingResponse)
async def generate_meeting_outcome_draft(
    meeting_id: uuid.UUID,
    member: TeamMember = Depends(require_moderator),
    session: AsyncSession = Depends(get_session),
):
    meeting = await meeting_service.get_meeting_by_id(session, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Встреча не найдена")
    try:
        processing = await meeting_ai_outcomes_service.generate_draft(session, meeting=meeting)
        await session.commit()
        return MeetingAIProcessingResponse.model_validate(processing)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/{meeting_id}/ai/publish", response_model=MeetingWithTasksResponse)
async def publish_meeting_outcomes(
    meeting_id: uuid.UUID,
    data: MeetingAIPublishRequest,
    member: TeamMember = Depends(require_moderator),
    session: AsyncSession = Depends(get_session),
):
    meeting = await meeting_service.get_meeting_by_id(session, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Встреча не найдена")
    processing = await meeting_ai_outcomes_service.processing_repo.get_or_create(session, meeting_id)
    tasks = await meeting_ai_outcomes_service.publish_outcomes(
        session,
        meeting=meeting,
        processing=processing,
        moderator=member,
        draft_summary=data.draft_summary,
        draft_decisions=data.draft_decisions,
        draft_tasks=[task.model_dump() for task in data.draft_tasks],
    )
    await session.commit()
    meeting = await meeting_service.get_meeting_by_id(session, meeting_id)
    return MeetingWithTasksResponse(meeting=_meeting_response(meeting), tasks_created=len(tasks))
```

- [ ] **Step 6: Run AI outcome tests**

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest tests/test_meeting_ai_outcomes_service.py tests/test_meeting_ai_outcomes_api.py -q
```

Expected: passes.

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/ai_service.py backend/app/services/meeting_ai_outcomes_service.py backend/app/api/meetings.py backend/tests/test_meeting_ai_outcomes_service.py backend/tests/test_meeting_ai_outcomes_api.py
git commit -m "feat: add meeting AI outcome drafts"
```

## Task 5: Frontend Types, API Client, and Board Helpers

**Files:**

- Modify: `frontend/src/lib/types.ts`
- Modify: `frontend/src/lib/api.ts`
- Create: `frontend/src/components/meetings/meetingBoardUtils.ts`
- Create: `frontend/src/components/meetings/meetingBoardUtils.test.ts`
- Modify: `frontend/package.json`

- [ ] **Step 1: Add failing helper tests**

Create `frontend/src/components/meetings/meetingBoardUtils.test.ts`:

```ts
import assert from "node:assert/strict";
import test from "node:test";
import { getMeetingBoardSectionMeta, isMeetingBoardTaskOverdue } from "./meetingBoardUtils.ts";
import type { Task } from "../../lib/types.ts";

function task(overrides: Partial<Task>): Task {
  return {
    id: "task-id",
    short_id: 1,
    title: "Task",
    description: null,
    checklist: [],
    labels: [],
    status: "in_progress",
    priority: "normal",
    assignee_id: null,
    created_by_id: null,
    meeting_id: null,
    source: "web",
    deadline: null,
    reminder_at: null,
    reminder_comment: null,
    reminder_sent_at: null,
    completed_at: null,
    created_at: "2026-05-07T00:00:00Z",
    updated_at: "2026-05-07T00:00:00Z",
    assignee: null,
    created_by: null,
    ...overrides,
  };
}

test("getMeetingBoardSectionMeta labels done section as done this week", () => {
  assert.equal(getMeetingBoardSectionMeta("done_this_week").label, "Выполнено за неделю");
});

test("isMeetingBoardTaskOverdue ignores done tasks", () => {
  assert.equal(isMeetingBoardTaskOverdue(task({ status: "done", deadline: "2026-05-01" }), new Date("2026-05-07")), false);
});
```

- [ ] **Step 2: Add test script entry and verify failure**

In `frontend/package.json`, add the new test file to `test`:

```json
"test": "node --test --experimental-strip-types src/lib/dateUtils.test.ts src/lib/compactHeaderControls.test.ts src/lib/taskUrgency.test.ts src/components/tasks/taskFilterUtils.test.ts src/components/tasks/taskLabelUtils.test.ts src/components/meetings/meetingBoardUtils.test.ts"
```

Run:

```bash
cd frontend && npm test
```

Expected: fails because `meetingBoardUtils.ts` does not exist.

- [ ] **Step 3: Add frontend types**

In `frontend/src/lib/types.ts`, update transcript source and add types:

```ts
export type MeetingTranscriptSource = "zoom_api" | "manual" | "openai_audio";
export type MeetingAIProcessingStatus =
  | "idle"
  | "recording_not_ready"
  | "recording_ready"
  | "transcribing"
  | "transcript_ready"
  | "draft_ready"
  | "published"
  | "failed";
export type MeetingBoardSectionKey = "urgent" | "in_progress" | "review" | "done_this_week";
```

Change `Meeting.transcript_source`:

```ts
transcript_source: MeetingTranscriptSource | null;
```

Add interfaces:

```ts
export interface MeetingBoardMaterial {
  id: string;
  title: string;
  url: string;
  description: string | null;
}

export interface MeetingBoardSettings {
  id: string;
  meeting_id: string;
  added_member_ids: string[];
  added_department_ids: string[];
  pinned_task_ids: string[];
  materials: MeetingBoardMaterial[];
  board_notes: string | null;
  created_by_id: string | null;
  updated_by_id: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface MeetingBoardResponse {
  meeting: Meeting;
  settings: MeetingBoardSettings;
  urgent: Task[];
  in_progress: Task[];
  review: Task[];
  done_this_week: Task[];
}

export interface MeetingAITaskDraft {
  title: string;
  description: string | null;
  assignee_name: string | null;
  assignee_id: string | null;
  deadline: string | null;
  priority: TaskPriority;
  selected: boolean;
}

export interface MeetingAIProcessing {
  id: string;
  meeting_id: string;
  status: MeetingAIProcessingStatus;
  transcript_source: MeetingTranscriptSource | null;
  transcription_model: string | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  transcript_char_count: number | null;
  audio_duration_seconds: number | null;
  estimated_cost_usd: string | null;
  draft_summary: string | null;
  draft_decisions: string[];
  draft_tasks: MeetingAITaskDraft[];
  published_at: string | null;
  published_by_id: string | null;
}
```

- [ ] **Step 4: Add API client methods**

In `frontend/src/lib/api.ts`, import the new types and add:

```ts
async getMeetingBoard(meetingId: string): Promise<MeetingBoardResponse> {
  return this.request<MeetingBoardResponse>(`/api/meetings/${meetingId}/board`);
}

async updateMeetingBoardSettings(
  meetingId: string,
  data: Partial<Pick<MeetingBoardSettings, "added_member_ids" | "added_department_ids" | "pinned_task_ids" | "materials" | "board_notes">>
): Promise<MeetingBoardSettings> {
  return this.request<MeetingBoardSettings>(`/api/meetings/${meetingId}/board/settings`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

async transcribeMeetingAudio(meetingId: string): Promise<MeetingAIProcessing> {
  return this.request<MeetingAIProcessing>(`/api/meetings/${meetingId}/ai/transcribe-audio`, {
    method: "POST",
  });
}

async generateMeetingOutcomeDraft(meetingId: string): Promise<MeetingAIProcessing> {
  return this.request<MeetingAIProcessing>(`/api/meetings/${meetingId}/ai/generate-draft`, {
    method: "POST",
  });
}

async publishMeetingOutcomes(
  meetingId: string,
  data: { draft_summary: string; draft_decisions: string[]; draft_tasks: MeetingAITaskDraft[] }
): Promise<MeetingWithTasksResponse> {
  return this.request<MeetingWithTasksResponse>(`/api/meetings/${meetingId}/ai/publish`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}
```

- [ ] **Step 5: Add board utility helpers**

Create `frontend/src/components/meetings/meetingBoardUtils.ts`:

```ts
import { parseLocalDate } from "@/lib/dateUtils";
import type { MeetingBoardSectionKey, Task } from "@/lib/types";

export const MEETING_BOARD_SECTIONS: MeetingBoardSectionKey[] = [
  "urgent",
  "in_progress",
  "review",
  "done_this_week",
];

export function getMeetingBoardSectionMeta(key: MeetingBoardSectionKey): {
  label: string;
  tone: string;
} {
  const meta: Record<MeetingBoardSectionKey, { label: string; tone: string }> = {
    urgent: { label: "Срочные", tone: "border-priority-urgent-fg/30 bg-priority-urgent-bg/60" },
    in_progress: { label: "В работе", tone: "border-status-progress-fg/25 bg-status-progress-bg/50" },
    review: { label: "На проверке", tone: "border-status-review-fg/25 bg-status-review-bg/50" },
    done_this_week: { label: "Выполнено за неделю", tone: "border-status-done-fg/25 bg-status-done-bg/50" },
  };
  return meta[key];
}

export function isMeetingBoardTaskOverdue(task: Task, now = new Date()): boolean {
  if (!task.deadline) return false;
  if (task.status === "done" || task.status === "cancelled") return false;
  const todayStart = new Date(now);
  todayStart.setHours(0, 0, 0, 0);
  return parseLocalDate(task.deadline) < todayStart;
}
```

- [ ] **Step 6: Run frontend helper tests**

```bash
cd frontend && npm test
```

Expected: passes.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/lib/types.ts frontend/src/lib/api.ts frontend/src/components/meetings/meetingBoardUtils.ts frontend/src/components/meetings/meetingBoardUtils.test.ts frontend/package.json
git commit -m "feat: add meeting board frontend types"
```

## Task 6: Frontend Meeting Board Route

**Files:**

- Create: `frontend/src/app/meetings/[id]/board/page.tsx`
- Create: `frontend/src/components/meetings/MeetingBoardHeader.tsx`
- Create: `frontend/src/components/meetings/MeetingBoardSection.tsx`
- Create: `frontend/src/components/meetings/MeetingBoardScopePanel.tsx`
- Create: `frontend/src/components/meetings/MeetingBoardMaterials.tsx`
- Modify: `frontend/src/app/meetings/[id]/page.tsx`

- [ ] **Step 1: Add board entry point to meeting detail**

In `frontend/src/app/meetings/[id]/page.tsx`, import `LayoutDashboard`:

```tsx
import { LayoutDashboard } from "lucide-react";
```

Near the Zoom + Participants row, add:

```tsx
<div className="flex justify-end animate-fade-in-up stagger-3">
  <Link href={`/meetings/${meeting.id}/board`}>
    <Button variant="outline" size="sm" className="rounded-xl gap-1.5">
      <LayoutDashboard className="h-4 w-4" />
      Открыть доску встречи
    </Button>
  </Link>
</div>
```

- [ ] **Step 2: Create board header**

Create `frontend/src/components/meetings/MeetingBoardHeader.tsx`:

```tsx
"use client";

import Link from "next/link";
import { ArrowLeft, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { Meeting, TeamMember } from "@/lib/types";
import { formatMeetingHeaderDateTime } from "@/lib/meetingDateTime";

export function MeetingBoardHeader({
  meeting,
  participants,
}: {
  meeting: Meeting;
  participants: TeamMember[];
}) {
  return (
    <header className="flex flex-col gap-3 border-b border-border/60 bg-background/95 px-5 py-4 backdrop-blur sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        <Link href={`/meetings/${meeting.id}`} className="mb-2 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-3.5 w-3.5" />
          К встрече
        </Link>
        <h1 className="truncate text-xl font-heading font-bold">
          {meeting.title || "Встреча без названия"}
        </h1>
        {meeting.meeting_date && (
          <p className="text-sm text-muted-foreground">
            {formatMeetingHeaderDateTime(meeting.meeting_date)}
          </p>
        )}
      </div>
      <Badge variant="outline" className="w-fit rounded-lg gap-1.5">
        <Users className="h-3.5 w-3.5" />
        {participants.length} участников
      </Badge>
    </header>
  );
}
```

- [ ] **Step 3: Create board section component**

Create `frontend/src/components/meetings/MeetingBoardSection.tsx`:

```tsx
"use client";

import { TaskCard } from "@/components/tasks/TaskCard";
import { getMeetingBoardSectionMeta, isMeetingBoardTaskOverdue } from "./meetingBoardUtils";
import type { MeetingBoardSectionKey, Task } from "@/lib/types";

export function MeetingBoardSection({
  sectionKey,
  tasks,
}: {
  sectionKey: MeetingBoardSectionKey;
  tasks: Task[];
}) {
  const meta = getMeetingBoardSectionMeta(sectionKey);
  return (
    <section className={`rounded-xl border p-3 ${meta.tone}`}>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-heading font-semibold">{meta.label}</h2>
        <span className="rounded-md bg-background/70 px-1.5 py-0.5 text-2xs font-semibold">
          {tasks.length}
        </span>
      </div>
      <div className="grid gap-2">
        {tasks.length === 0 ? (
          <div className="min-h-28 rounded-lg border border-dashed border-border/50 bg-background/45" />
        ) : (
          tasks.map((task) => (
            <div key={task.id} className={isMeetingBoardTaskOverdue(task) ? "ring-1 ring-destructive/25 rounded-xl" : ""}>
              <TaskCard task={task} />
            </div>
          ))
        )}
      </div>
    </section>
  );
}
```

- [ ] **Step 4: Create scope panel and materials components**

Create `frontend/src/components/meetings/MeetingBoardScopePanel.tsx`:

```tsx
"use client";

import { UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Department, MeetingBoardSettings, TeamMember } from "@/lib/types";

export function MeetingBoardScopePanel({
  settings,
  isModerator,
}: {
  settings: MeetingBoardSettings;
  members: TeamMember[];
  departments: Department[];
  isModerator: boolean;
}) {
  return (
    <aside className="rounded-xl border border-border/60 bg-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-heading font-semibold">Состав доски</h2>
        {isModerator && (
          <Button variant="outline" size="sm" className="h-8 rounded-lg gap-1.5">
            <UserPlus className="h-3.5 w-3.5" />
            Добавить
          </Button>
        )}
      </div>
      <div className="space-y-2 text-xs text-muted-foreground">
        <p>Добавлено людей: {settings.added_member_ids.length}</p>
        <p>Добавлено отделов: {settings.added_department_ids.length}</p>
        <p>Закреплено задач: {settings.pinned_task_ids.length}</p>
      </div>
    </aside>
  );
}
```

Create `frontend/src/components/meetings/MeetingBoardMaterials.tsx`:

```tsx
"use client";

import { LinkIcon, StickyNote } from "lucide-react";
import type { MeetingBoardSettings } from "@/lib/types";

export function MeetingBoardMaterials({ settings }: { settings: MeetingBoardSettings }) {
  return (
    <aside className="rounded-xl border border-border/60 bg-card p-4">
      <h2 className="mb-3 flex items-center gap-2 text-sm font-heading font-semibold">
        <LinkIcon className="h-4 w-4" />
        Материалы
      </h2>
      <div className="space-y-2">
        {settings.materials.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border/60 py-6 text-center text-xs text-muted-foreground">
            Материалы пока не добавлены
          </div>
        ) : (
          settings.materials.map((material) => (
            <a key={material.id} href={material.url} target="_blank" rel="noreferrer" className="block rounded-lg border border-border/60 px-3 py-2 text-sm hover:bg-muted/40">
              {material.title}
            </a>
          ))
        )}
      </div>
      {settings.board_notes && (
        <div className="mt-4 rounded-lg bg-muted/40 p-3 text-sm">
          <p className="mb-1 flex items-center gap-1.5 text-xs text-muted-foreground">
            <StickyNote className="h-3.5 w-3.5" />
            Заметки
          </p>
          <p className="whitespace-pre-wrap">{settings.board_notes}</p>
        </div>
      )}
    </aside>
  );
}
```

- [ ] **Step 5: Create board page**

Create `frontend/src/app/meetings/[id]/board/page.tsx`:

```tsx
"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { Skeleton } from "@/components/ui/skeleton";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { useDepartments } from "@/hooks/useDepartments";
import { useTeam } from "@/hooks/useTeam";
import { api } from "@/lib/api";
import { PermissionService } from "@/lib/permissions";
import type { MeetingBoardResponse, MeetingBoardSectionKey, TeamMember } from "@/lib/types";
import { MeetingBoardHeader } from "@/components/meetings/MeetingBoardHeader";
import { MeetingBoardSection } from "@/components/meetings/MeetingBoardSection";
import { MeetingBoardScopePanel } from "@/components/meetings/MeetingBoardScopePanel";
import { MeetingBoardMaterials } from "@/components/meetings/MeetingBoardMaterials";
import { MEETING_BOARD_SECTIONS } from "@/components/meetings/meetingBoardUtils";

export default function MeetingBoardPage() {
  const params = useParams();
  const meetingId = params.id as string;
  const { user } = useCurrentUser();
  const { members } = useTeam();
  const { departments } = useDepartments();
  const [board, setBoard] = useState<MeetingBoardResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getMeetingBoard(meetingId).then(setBoard).finally(() => setLoading(false));
  }, [meetingId]);

  const participants = useMemo(() => {
    if (!board) return [] as TeamMember[];
    const byId = new Map(members.map((member) => [member.id, member]));
    return board.meeting.participant_ids.map((id) => byId.get(id)).filter((member): member is TeamMember => Boolean(member));
  }, [board, members]);

  if (loading || !board) {
    return <div className="space-y-4 p-5"><Skeleton className="h-20 rounded-xl" /><Skeleton className="h-96 rounded-xl" /></div>;
  }

  const isModerator = user ? PermissionService.isModerator(user) : false;

  return (
    <div className="min-h-screen bg-background">
      <MeetingBoardHeader meeting={board.meeting} participants={participants} />
      <main className="grid gap-4 p-5 xl:grid-cols-[280px_minmax(0,1fr)_280px]">
        <MeetingBoardScopePanel settings={board.settings} members={members} departments={departments} isModerator={isModerator} />
        <div className="grid gap-4 lg:grid-cols-2 2xl:grid-cols-4">
          {MEETING_BOARD_SECTIONS.map((sectionKey: MeetingBoardSectionKey) => (
            <MeetingBoardSection key={sectionKey} sectionKey={sectionKey} tasks={board[sectionKey]} />
          ))}
        </div>
        <MeetingBoardMaterials settings={board.settings} />
      </main>
    </div>
  );
}
```

- [ ] **Step 6: Verify frontend route**

Run:

```bash
cd frontend && npm test && npx tsc --noEmit && npm run lint
```

Expected: tests, TypeScript, and lint pass.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/app/meetings/[id]/page.tsx frontend/src/app/meetings/[id]/board/page.tsx frontend/src/components/meetings/MeetingBoardHeader.tsx frontend/src/components/meetings/MeetingBoardSection.tsx frontend/src/components/meetings/MeetingBoardScopePanel.tsx frontend/src/components/meetings/MeetingBoardMaterials.tsx
git commit -m "feat: add shareable meeting board"
```

## Task 7: Frontend AI Outcomes Panel

**Files:**

- Create: `frontend/src/components/meetings/MeetingAiOutcomesPanel.tsx`
- Modify: `frontend/src/app/meetings/[id]/page.tsx`

- [ ] **Step 1: Create AI outcomes panel**

Create `frontend/src/components/meetings/MeetingAiOutcomesPanel.tsx`:

```tsx
"use client";

import { useState } from "react";
import { Bot, FileAudio, Loader2, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/shared/Toast";
import { api } from "@/lib/api";
import type { MeetingAIProcessing, MeetingAITaskDraft } from "@/lib/types";

export function MeetingAiOutcomesPanel({
  meetingId,
  isModerator,
  onPublished,
}: {
  meetingId: string;
  isModerator: boolean;
  onPublished: () => void;
}) {
  const { toastSuccess, toastError } = useToast();
  const [processing, setProcessing] = useState<MeetingAIProcessing | null>(null);
  const [busy, setBusy] = useState(false);
  const [summary, setSummary] = useState("");
  const [decisionsText, setDecisionsText] = useState("");
  const [tasks, setTasks] = useState<MeetingAITaskDraft[]>([]);

  if (!isModerator) return null;

  async function handleTranscribe() {
    setBusy(true);
    try {
      const result = await api.transcribeMeetingAudio(meetingId);
      setProcessing(result);
      toastSuccess("Транскрипция аудио готова");
    } catch (e) {
      toastError(e instanceof Error ? e.message : "Ошибка транскрибации");
    } finally {
      setBusy(false);
    }
  }

  async function handleGenerateDraft() {
    setBusy(true);
    try {
      const result = await api.generateMeetingOutcomeDraft(meetingId);
      setProcessing(result);
      setSummary(result.draft_summary || "");
      setDecisionsText(result.draft_decisions.join("\\n"));
      setTasks(result.draft_tasks);
    } catch (e) {
      toastError(e instanceof Error ? e.message : "Ошибка генерации итогов");
    } finally {
      setBusy(false);
    }
  }

  async function handlePublish() {
    setBusy(true);
    try {
      await api.publishMeetingOutcomes(meetingId, {
        draft_summary: summary,
        draft_decisions: decisionsText.split("\\n").map((line) => line.trim()).filter(Boolean),
        draft_tasks: tasks,
      });
      toastSuccess("Итоги встречи опубликованы");
      onPublished();
    } catch (e) {
      toastError(e instanceof Error ? e.message : "Ошибка публикации итогов");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="rounded-2xl border border-border/60 bg-card p-4">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-sm font-heading font-semibold">
            <Bot className="h-4 w-4 text-primary" />
            AI-итоги после встречи
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Запуск только вручную. Аудио не сохраняется в портале.
          </p>
        </div>
        {busy && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
      </div>

      <div className="flex flex-wrap gap-2">
        <Button type="button" variant="outline" size="sm" onClick={handleTranscribe} disabled={busy} className="rounded-xl gap-1.5">
          <FileAudio className="h-4 w-4" />
          Транскрибировать аудио
        </Button>
        <Button type="button" variant="outline" size="sm" onClick={handleGenerateDraft} disabled={busy} className="rounded-xl gap-1.5">
          <Bot className="h-4 w-4" />
          Создать черновик итогов
        </Button>
      </div>

      {(processing?.status === "draft_ready" || summary) && (
        <div className="mt-4 space-y-3">
          <Textarea value={summary} onChange={(e) => setSummary(e.target.value)} rows={4} placeholder="Резюме встречи" />
          <Textarea value={decisionsText} onChange={(e) => setDecisionsText(e.target.value)} rows={4} placeholder="Решения, каждое с новой строки" />
          <div className="space-y-2">
            {tasks.map((task, index) => (
              <label key={`${task.title}-${index}`} className="flex items-start gap-2 rounded-lg border border-border/60 p-3 text-sm">
                <input
                  type="checkbox"
                  checked={task.selected}
                  onChange={(e) =>
                    setTasks((current) =>
                      current.map((item, itemIndex) =>
                        itemIndex === index ? { ...item, selected: e.target.checked } : item
                      )
                    )
                  }
                />
                <span>{task.title}</span>
              </label>
            ))}
          </div>
          <Button type="button" onClick={handlePublish} disabled={busy} className="rounded-xl gap-1.5">
            <Send className="h-4 w-4" />
            Опубликовать итоги
          </Button>
        </div>
      )}
    </section>
  );
}
```

- [ ] **Step 2: Mount panel on meeting detail**

In `frontend/src/app/meetings/[id]/page.tsx`, import:

```tsx
import { MeetingAiOutcomesPanel } from "@/components/meetings/MeetingAiOutcomesPanel";
```

Render it after the Zoom + Participants row:

```tsx
<MeetingAiOutcomesPanel
  meetingId={meeting.id}
  isModerator={isModerator}
  onPublished={fetchData}
/>
```

- [ ] **Step 3: Verify frontend**

```bash
cd frontend && npm test && npx tsc --noEmit && npm run lint && npm run build
```

Expected: passes.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/meetings/MeetingAiOutcomesPanel.tsx frontend/src/app/meetings/[id]/page.tsx
git commit -m "feat: add meeting AI outcomes panel"
```

## Task 8: Documentation, Full Verification, and Browser QA

**Files:**

- Modify: `docs/PLAN.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/TEST_PLAN.md`

- [ ] **Step 1: Update status and test plan**

Append to `docs/STATUS.md`:

```markdown
## Meeting Board and AI Outcomes

- Current phase: implemented, verification in progress
- Spec: `docs/superpowers/specs/2026-05-07-meeting-board-and-ai-outcomes-design.md`
- Plan: `docs/superpowers/plans/2026-05-07-meeting-board-and-ai-outcomes.md`
- Scope: shareable meeting board, manual Zoom audio transcription, moderator-reviewed AI outcomes
- Latest progress:
  - Meeting board backend and frontend surfaces are implemented.
  - Manual audio transcription stores only transcript text and metadata.
  - AI outcome drafts require moderator confirmation before tasks are created.
```

Append to `docs/TEST_PLAN.md`:

```markdown
## Meeting Board and AI Outcomes

### Automated

- `cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest tests/test_meeting_board_service.py tests/test_meeting_board_api.py tests/test_meeting_ai_outcomes_service.py tests/test_meeting_ai_outcomes_api.py -q`
- `cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest -q`
- `cd frontend && npm test`
- `cd frontend && npx tsc --noEmit`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- `git diff --check`

### Manual

1. Open a meeting and use `Открыть доску встречи`.
2. Confirm the board is usable at a Zoom screen-share desktop width.
3. Confirm urgent, in-progress, review, and done-this-week sections render.
4. Add a member, department, pinned task, link, and board note as a moderator.
5. Confirm regular participants cannot edit board composition.
6. Run manual audio transcription on a meeting with a Zoom recording.
7. Confirm no audio file is stored in portal storage after processing.
8. Generate an AI outcome draft and edit summary, decisions, and task candidates.
9. Publish with one task candidate unchecked and confirm only selected tasks are created.
```

- [ ] **Step 2: Run full backend verification**

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest tests/test_meeting_board_service.py tests/test_meeting_board_api.py tests/test_meeting_ai_outcomes_service.py tests/test_meeting_ai_outcomes_api.py -q
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest -q
```

Expected: targeted tests and full backend suite pass.

- [ ] **Step 3: Run full frontend verification**

```bash
cd frontend && npm test
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
cd frontend && npm run build
```

Expected: all frontend checks pass.

- [ ] **Step 4: Run repository diff check**

```bash
git diff --check
```

Expected: no whitespace errors.

- [ ] **Step 5: Browser QA**

Start the frontend and backend as required by the local environment. Then check:

```bash
cd frontend && npm run dev
```

Open:

- `http://127.0.0.1:3000/meetings`
- a meeting detail page;
- `/meetings/{id}/board`.

Expected:

- meeting detail shows the board button and AI outcomes panel for moderators;
- board route renders without admin tabs;
- board sections fit desktop screen-share widths;
- unauthenticated users are redirected through existing auth behavior.

- [ ] **Step 6: Commit docs and final status**

```bash
git add docs/PLAN.md docs/STATUS.md docs/TEST_PLAN.md
git commit -m "docs: record meeting board outcomes verification"
```

## Final Validation Commands

Run these before claiming completion:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest tests/test_meeting_board_service.py tests/test_meeting_board_api.py tests/test_meeting_ai_outcomes_service.py tests/test_meeting_ai_outcomes_api.py -q
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest -q
cd frontend && npm test
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
cd frontend && npm run build
git diff --check
```
