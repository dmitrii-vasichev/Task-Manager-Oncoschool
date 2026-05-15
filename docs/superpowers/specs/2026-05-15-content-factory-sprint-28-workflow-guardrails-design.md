# Content Factory Sprint 28 Workflow Guardrails Design

## Context

Sprint 26 added quick workflow actions for publications. Sprint 27 made status moves visible in publication history. The remaining safety gap is that the direct publication PATCH endpoint still accepts any status jump. A user or client can accidentally move a draft directly to `published`, or schedule an approved publication without a planned date.

## Goal

Add backend workflow guardrails and matching frontend affordances so publication status changes follow the intended editorial path.

## Scope

In scope:

- Backend validates status transitions inside `PublicationService.update`.
- Backend rejects invalid transitions with a 400 response and a readable Russian error message.
- Backend allows metadata-only edits without applying transition validation.
- Backend allows one update to set `scheduled_at` and move `approved -> scheduled`.
- Backend rejects `approved -> scheduled` when no planned date exists in either the current publication or payload.
- Backend allows `approved -> published` and `scheduled -> published` for manual publish fact capture.
- Frontend disables the publish fact button until a publication is `approved`, `scheduled`, or already `published`.
- Frontend shows a readable hint when the publish fact action is not available yet.
- Tests cover service validation, API error handling, frontend helper behavior, and source guards.
- Durable documentation updates.

Out of scope:

- New database tables, migrations, or workflow event tables.
- User comments on transitions.
- Role-specific transition permissions.
- Automatic publishing or external platform integrations.
- Full transition editor UI.
- Bulk status updates.

## Backend Design

`PublicationService.update` remains the status-change gateway. Before applying changes, it will:

- Capture `old_status`.
- Derive `new_status` from the PATCH payload.
- If the status is unchanged or absent, skip transition validation.
- Validate `new_status` against an explicit adjacency map.
- Validate schedule readiness for `approved -> scheduled`.
- Raise a small domain exception, `PublicationWorkflowTransitionError`, when the transition is invalid.

Allowed status moves:

- `draft -> needs_copy | cancelled`
- `needs_copy -> needs_design | factcheck | cancelled`
- `needs_design -> factcheck | cancelled`
- `factcheck -> doctor_review | needs_copy | cancelled`
- `doctor_review -> approved | needs_copy | cancelled`
- `approved -> scheduled | doctor_review | cancelled | published`
- `scheduled -> approved | cancelled | published`
- `failed -> needs_copy | cancelled`
- `cancelled -> draft`
- `published` has no outgoing status move in this sprint, but can still receive metadata-only updates.

The publication PATCH route catches `PublicationWorkflowTransitionError` and returns HTTP 400 with the exception message. It still returns 404 when the publication is missing.

## Frontend Design

`getContentFactoryPublicationOperations` will expose:

- `canSavePublishFact`
- `publishFactDisabledReason`

The operations panel will:

- Keep the existing `Факт публикации` dialog for `approved`, `scheduled`, and `published` records.
- Disable the publish fact button for early workflow statuses.
- Show `Сначала доведите публикацию до одобрения или календаря.` as the disabled reason.
- Keep the existing published-state editing path for updating actual date, post URL, and post ID.

This is intentionally not a full workflow wizard. Quick status actions remain the primary way to move records through editorial production.

## Testing

Backend:

- Service test rejects `draft -> published`.
- Service test rejects `approved -> scheduled` without a planned date.
- Service test allows `approved -> scheduled` when `scheduled_at` is provided in the same payload.
- API test maps `PublicationWorkflowTransitionError` to HTTP 400 and does not commit.

Frontend:

- Utility test proves draft publications cannot save publish facts yet and receive the Russian disabled reason.
- Utility test proves approved, scheduled, and published publications can save publish facts.
- Source guard verifies the operations panel uses `canSavePublishFact`, `publishFactDisabledReason`, and disables the button.

## Manual Checks

1. Open a draft publication detail page.
2. Confirm the publish fact button is disabled and explains that approval or calendar is required first.
3. Move the publication through quick actions to `approved`.
4. Confirm the publish fact dialog can open.
5. Try setting `scheduled` without a planned date through the API and confirm a 400 error.
6. Set a planned date and move to `scheduled`; confirm the transition succeeds and appears in history.
7. Mark an approved or scheduled publication as published through the dialog.
8. Confirm published records can still update the publication fact.
