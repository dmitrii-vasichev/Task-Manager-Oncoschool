# Content Factory Sprint 26 Publication Workflow Actions Design

## Context

Sprint 25 made `/content-factory/review` an operational triage screen. It now explains which publications need attention and what the team should do next. The remaining gap is execution: users still need to open the full edit dialog and manually pick a status from a generic dropdown to move a publication through the workflow.

The existing backend already supports `PATCH /api/content-factory/publications/{id}` through `api.updateCFPublication`, and the publication edit dialog already sends `status`. Sprint 26 uses that existing contract to add clear quick actions on the publication detail page.

## Goal

Let a user move a publication to the next workflow step from the publication detail page without opening the large edit form.

## Scope

In scope:

- A pure frontend helper that derives available workflow actions from the current publication status and schedule.
- Russian labels, descriptions, and action categories for workflow buttons.
- A compact `Быстрые действия` panel on `/content-factory/publications/[id]`.
- Status updates through the existing `api.updateCFPublication` endpoint.
- Guardrails for actions that require extra fields:
  - Scheduling requires `scheduled_at`; if missing, the action explains that a date is needed.
  - Publishing remains handled by the existing `Факт публикации` dialog because it needs actual publication date and post reference.
- Source guards and helper tests.
- Durable documentation updates.

Out of scope:

- New backend endpoints.
- Backend transition validation.
- Approval comments, audit log events, assignments, notifications, or mentions.
- Bulk status changes.
- Automatic publishing or platform API integrations.
- Replacing the full publication edit dialog.

## Workflow Model

The helper `getContentFactoryPublicationWorkflowActions(publication)` returns an ordered list of actions. Each action contains:

- `key`: stable frontend action id.
- `targetStatus`: next `CFPublicationStatus`.
- `label`: button label.
- `description`: one sentence for the UI.
- `tone`: visual intent (`primary`, `default`, `warning`, `danger`, or `muted`).
- `disabled`: whether the user can run the action immediately.
- `disabledReason`: readable reason when disabled.

Initial mapping:

- `draft`:
  - `Отправить в производство` -> `needs_copy`
  - `Отменить` -> `cancelled`
- `needs_copy`:
  - `Передать на дизайн` -> `needs_design`
  - `На фактчек` -> `factcheck`
  - `Отменить` -> `cancelled`
- `needs_design`:
  - `На фактчек` -> `factcheck`
  - `Отменить` -> `cancelled`
- `factcheck`:
  - `На проверку врача` -> `doctor_review`
  - `Вернуть в текст` -> `needs_copy`
  - `Отменить` -> `cancelled`
- `doctor_review`:
  - `Одобрить` -> `approved`
  - `Вернуть в текст` -> `needs_copy`
  - `Отменить` -> `cancelled`
- `approved`:
  - `Поставить в календарь` -> `scheduled`; disabled when `scheduled_at` is missing.
  - `Вернуть врачу` -> `doctor_review`
  - `Отменить` -> `cancelled`
- `scheduled`:
  - `Вернуть к одобрению` -> `approved`
  - `Отменить` -> `cancelled`
- `failed`:
  - `Вернуть в производство` -> `needs_copy`
  - `Отменить` -> `cancelled`
- `cancelled`:
  - `Вернуть в черновик` -> `draft`
- `published`:
  - No quick status transition. The panel explains that facts and metrics are handled below.

## UI Design

The new panel should sit in the right sidebar of the publication detail page near the existing `Публикация и статистика` panel. It should be dense and utilitarian:

- Header: `Быстрые действия`.
- Supporting copy: one sentence explaining that actions update only the workflow status.
- Current status badge remains visible in the page header.
- Each action is a full-width button with a short helper line below or inside the row.
- Disabled actions are visible with the reason, not hidden.
- While an action is saving, buttons are disabled and the active button shows a spinner.
- Successful save refreshes the detail page through the existing `onSaved` callback.

The panel must avoid nested cards and should not make the sidebar visually heavy. It should use the existing design language from `ContentFactoryPublicationOperationsPanel`.

## Error Handling

- API failure shows the existing toast error pattern.
- Disabled scheduling action shows `Сначала укажите плановую дату`.
- Unknown or unsupported statuses show a calm empty state: `Для этого статуса быстрых действий нет`.
- The existing full edit dialog remains available for complex updates.

## Testing

Automated coverage:

- Helper test for action mapping by status.
- Helper test for disabled schedule action when `scheduled_at` is missing.
- Helper test for no quick actions on `published`.
- Source guard that the publication detail page renders `ContentFactoryPublicationWorkflowActionsPanel`.
- Source guard that the panel calls `getContentFactoryPublicationWorkflowActions` and `api.updateCFPublication`.

Manual checks:

- Open a publication detail page in several statuses.
- Confirm `Быстрые действия` appears in the sidebar.
- Click a status action and confirm the status badge refreshes.
- Confirm `Поставить в календарь` is disabled without planned date.
- Confirm published publications show the explanatory empty state.

