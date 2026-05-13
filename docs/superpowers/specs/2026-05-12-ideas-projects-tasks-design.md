# Ideas, Projects, and Tasks Design

## Metadata

| Field | Value |
| --- | --- |
| Date | 2026-05-12 |
| Status | Ready for user review |
| Source | `ideas_oncoschool (2).pdf` |
| Feature | Ideas workflow with a future Projects layer |
| Phase 1 Scope | Web portal Ideas section |
| Phase 2 Scope | Projects as a separate planning layer |

## Source Summary

The source presentation describes a new Ideas block for the Oncoschool portal:

- collect improvement proposals in a managed inbox;
- assign responsibility for review and decisions;
- keep decision history visible;
- prevent "ideas without deadlines" from polluting the task board;
- convert approved ideas into real tasks;
- reduce repeated discussions by making decisions and rationale explicit.

This design keeps that story, but expands it into a phased product model:

```text
Idea -> Tasks
Idea -> Project -> Tasks
Project -> Tasks
```

Phase 1 proves the ideas workflow. Phase 2 adds Projects without requiring the Phase 1 data model or UX to be rewritten.

## Product Model

### Idea

An Idea is an incoming proposal. It answers:

> Should we do this?

An idea is not a task and not a project. It stores the proposal, discussion, review owner, decision, involved departments, department-level implementation progress, and links to tasks created from the idea.

### Project

A Project is a larger approved initiative. It answers:

> How do we organize this implementation?

Projects are deferred to Phase 2. A future project can be created from an accepted idea or directly without an idea. Projects will group departments, milestones or stages, and tasks.

### Task

A Task is concrete work for a specific assignee. It answers:

> Who does what?

Phase 1 reuses the existing task board and task model. Tasks created from ideas remain normal portal tasks.

## Goals

- Add a dedicated web portal section named `Идеи`.
- Let every active team member create ideas and see the shared ideas register.
- Keep ideas out of the task board until an explicit decision turns them into work.
- Support a review flow with responsible ownership and decision history.
- Support multi-department implementation for accepted ideas.
- Let each involved department create and track its own related tasks.
- Let the idea reach `Завершена` only after all required department work is finished, or after all direct linked tasks are closed when no departments are involved.
- Preserve existing task permissions when showing linked task details.
- Document the future Projects layer so Phase 1 remains compatible with Phase 2.

## Non-Goals

- No Telegram bot entry point in Phase 1.
- No standalone Projects implementation in Phase 1.
- No idea labels, tags, or separate theme taxonomy in Phase 1.
- No analytics dashboard for ideas in Phase 1.
- No automatic AI decomposition of ideas into tasks in Phase 1.
- No voting, likes, duplicate detection, templates, or SLA automation in Phase 1.
- No changes to the existing task board visibility model.

## Phase 1: Ideas

### Navigation

Add a new main portal section:

```text
Идеи
```

The section contains:

- `/ideas` — ideas register;
- `/ideas/{id}` — idea detail page.

### Ideas Register

The `/ideas` page is a list/register, not a kanban board and not a dashboard.

Primary controls:

- `Новая идея` button;
- status tabs:
  - `Все`;
  - `Новые`;
  - `На рассмотрении`;
  - `Принятые`;
  - `В задачах`;
  - `Завершенные`;
  - `Отложенные`;
  - `Отклоненные`;
- filters:
  - review owner;
  - author;
  - involved department;
  - created date range.

Each idea row/card shows:

- title;
- status;
- author;
- review owner;
- involved departments;
- department progress, such as `2/3 departments ready`;
- linked task count;
- created date;
- last updated date.

### Create Idea

The create flow must stay short.

Required fields:

- title;
- description;
- review owner.

Optional fields:

- involved departments.

After creation, the idea status is `new`.

### Idea Detail Page

The `/ideas/{id}` page contains:

- title, status, author, and review owner;
- description;
- decision block;
- involved department implementation block;
- linked tasks;
- comments/discussion;
- event history.

The detail page is a standalone page so ideas can be linked directly and can grow without being constrained by a modal.

## Idea Status Model

### Statuses

Use these idea statuses:

| Status | User Label | Meaning |
| --- | --- | --- |
| `new` | `Новая` | Created but not yet actively reviewed. |
| `in_review` | `На рассмотрении` | A review owner is considering or discussing the idea. |
| `accepted` | `Принята` | Approved, but implementation tasks may not exist yet. |
| `in_tasks` | `В задачах` | Implementation has started through linked tasks or department work. |
| `completed` | `Завершена` | All required department contributions are complete and the idea is closed. |
| `rejected` | `Отклонена` | Explicitly declined with a required reason. |
| `deferred` | `Отложена` | Postponed with a required reason and optional revisit date. |

Primary lifecycle:

```text
Новая -> На рассмотрении -> Принята -> В задачах -> Завершена
```

Side states:

```text
Отклонена
Отложена
```

### Decision Rules

- Accepting an idea may include a comment, but the comment is optional.
- Rejecting an idea requires a reason.
- Deferring an idea requires a reason.
- A deferred idea may also store an optional revisit date.
- Moving to `in_tasks` happens when implementation begins, either by creating at least one linked task or by starting department-level work.
- Moving to `completed` is a manual action by the review owner, an admin, or a moderator.
- Completion is available when every involved department is either `ready` or `not_required`.
- If an accepted idea has no involved departments, completion is available only after it has at least one direct linked task and all direct linked tasks are completed or cancelled.

## Department Implementation

Accepted ideas can involve one or more departments.

Each involved department has:

- department;
- department implementation owner;
- contribution status;
- optional contribution note;
- linked tasks for that department;
- task progress summary.

Department contribution statuses:

| Status | User Label | Meaning |
| --- | --- | --- |
| `not_started` | `Не начато` | Department is involved but has not started implementation. |
| `in_progress` | `В работе` | Department has started work or has open related tasks. |
| `ready` | `Готово` | Department has completed its part. |
| `not_required` | `Не требуется` | Department was considered but no longer needs to contribute. |

### Department Completion

The system shows progress, for example:

```text
2 of 3 departments ready
5 of 8 linked tasks closed
```

The system should not silently complete an idea. It enables the final action when all departments are `ready` or `not_required`; the final close remains a deliberate action.

### Task Progress

For an involved department:

- open tasks keep the department visibly unfinished;
- completed or cancelled tasks count as closed;
- a department can be marked `ready` when it has no linked tasks yet, or when every linked task for that department is completed or cancelled;
- a department can still be marked `not_required` when no work is needed or when the department was attached by mistake;
- marking a department `ready` should be allowed by the same roles that can manage that department contribution.

## Permissions

### Everyone

Every active team member can:

- view the shared ideas register;
- view idea detail pages;
- create ideas;
- comment on ideas.

### Review Owner

The idea review owner can:

- move the idea to review;
- accept, reject, or defer the idea;
- add involved departments;
- assign department implementation owners;
- create linked tasks;
- complete the idea when completion rules are satisfied.

### Admins And Moderators

Admins and moderators can perform all idea actions on all ideas, including:

- changing the review owner;
- changing involved departments;
- changing department owners;
- correcting statuses;
- completing or reopening ideas.

### Department Head

The existing `departments.head_id` field defines the department head.

A department head can:

- add their own department to an accepted idea;
- assign or change the implementation owner for their department;
- create linked tasks for their department;
- mark their department contribution as `ready` or `not_required`.

### Department Implementation Owner

The department implementation owner can:

- manage their department's implementation block;
- create linked tasks for that department;
- mark the department contribution as `ready` when work is complete.

### Linked Task Visibility

Ideas are intentionally visible to the whole active team in Phase 1.

Linked task details still respect existing task permissions:

- aggregate task counts and department progress are visible on the idea;
- task titles, task details, and task links are shown only when the current user can see the task under existing task visibility rules;
- users without task visibility see a neutral hidden-task row or count, not hidden task content.

## Phase 1 Data Model

### `ideas`

Stores the idea itself.

Core fields:

- `id`;
- `title`;
- `description`;
- `status`;
- `author_id`;
- `review_owner_id`;
- `decision_comment`;
- `decision_by_id`;
- `decision_at`;
- `deferred_until`;
- `created_at`;
- `updated_at`;
- `completed_at`;

### `idea_departments`

Stores department-level implementation.

Core fields:

- `id`;
- `idea_id`;
- `department_id`;
- `owner_id`;
- `status`;
- `note`;
- `created_by_id`;
- `created_at`;
- `updated_at`;

Each idea can have a department at most once.

### `idea_tasks`

Stores links between ideas and existing tasks.

Core fields:

- `id`;
- `idea_id`;
- `idea_department_id`;
- `task_id`;
- `created_by_id`;
- `created_at`;

The department link is nullable so an idea can have general linked tasks, but department-scoped task creation should set it.

### `idea_comments`

Stores discussion.

Core fields:

- `id`;
- `idea_id`;
- `author_id`;
- `body`;
- `created_at`;
- `updated_at`;

### `idea_events`

Stores audit/history events.

Core fields:

- `id`;
- `idea_id`;
- `actor_id`;
- `event_type`;
- `payload`;
- `created_at`;

Events should cover:

- idea created;
- status changed;
- decision recorded;
- department added or updated;
- linked task created or attached;
- comment added;
- idea completed or reopened.

## Phase 1 API Shape

The detailed implementation plan will define exact request and response schemas. The expected API surface is:

- `GET /api/ideas`;
- `POST /api/ideas`;
- `GET /api/ideas/{id}`;
- `PATCH /api/ideas/{id}`;
- `POST /api/ideas/{id}/status`;
- `POST /api/ideas/{id}/comments`;
- `GET /api/ideas/{id}/events`;
- `POST /api/ideas/{id}/departments`;
- `PATCH /api/ideas/{id}/departments/{idea_department_id}`;
- `POST /api/ideas/{id}/departments/{idea_department_id}/tasks`;
- `POST /api/ideas/{id}/tasks`.

Task creation from an idea should reuse the existing task service so task permissions, notifications, labels, urgency, deadlines, and assignee rules remain consistent with the rest of the portal.

## Phase 1 Frontend Components

Expected frontend areas:

- add `Идеи` to the sidebar;
- create `/ideas` page;
- create `/ideas/[id]` page;
- add idea create dialog or page-level form;
- add status tabs and filters;
- add idea status badge;
- add idea decision panel;
- add department implementation panel;
- add linked task list;
- add comment thread;
- add event history.

The visual style should follow the existing portal design system:

- shadcn/ui primitives;
- Tailwind theme tokens;
- existing badge/card/table styles where appropriate;
- Lucide icons where icons help command recognition.

## Phase 2: Projects

Phase 2 adds a separate `Projects` layer.

Projects should support:

- creation from an accepted idea;
- direct creation without an idea;
- project owner;
- involved departments;
- milestones or stages;
- linked tasks;
- progress by department and task completion;
- project detail page;
- project list/register.

Future relationships:

```text
ideas.project_id -> projects.id
tasks.project_id -> projects.id
project_tasks.task_id -> tasks.id
```

Phase 2 should not remove direct `Idea -> Tasks` support. Small ideas can still become tasks without a project.

## Future Enhancements

- Telegram bot idea creation.
- Idea dashboard with review and implementation metrics.
- Review SLA and overdue review indicators.
- Voting or lightweight support signals.
- Duplicate detection.
- Idea templates.
- AI-assisted idea decomposition.
- Project-level notifications and summaries.
- Idea/project reporting.

## Test And Validation Strategy

Phase 1 implementation should include:

- backend tests for idea CRUD and status transitions;
- backend tests for required decision reasons;
- backend tests for department contribution permissions;
- backend tests for department completion and direct-task completion gating idea completion;
- backend tests for linked task creation through the existing task service;
- backend tests that linked task details respect existing task visibility;
- frontend tests for register filters and status tabs;
- frontend tests for idea create form validation;
- frontend tests for decision panel behavior;
- frontend tests for department implementation progress;
- TypeScript, lint, production build, and `git diff --check`.

## Acceptance Criteria

- A user can create an idea from the web portal with title, description, and review owner.
- Every active user can see the shared idea register.
- Ideas can be filtered by status, author, review owner, involved department, and created date range.
- An idea detail page shows the idea, decision, departments, linked tasks, comments, and event history.
- Rejected and deferred ideas require a reason.
- Accepted ideas can involve multiple departments.
- Each involved department can have its own owner, status, and linked tasks.
- Department heads can add their own department to an accepted idea.
- Review owners, department owners, admins, and moderators can create linked tasks within their allowed scope.
- The idea can move to `completed` only when all involved departments are `ready` or `not_required`, or when a no-department idea has only closed direct linked tasks.
- Linked task content does not leak beyond existing task visibility permissions.
- Projects are documented as Phase 2 and do not block the Phase 1 Ideas release.
