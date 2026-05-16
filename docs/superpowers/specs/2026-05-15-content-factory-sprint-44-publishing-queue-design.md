# Content Factory Sprint 44 Publishing Queue Design

## Context

Wave C starts controlled publishing automation. The current system supports manual handoff packages, saved channel variants, publication facts, post URLs, and metric evidence. It does not yet have a durable place where an approved or scheduled publication can be queued for automated delivery, retried, audited, or routed back to manual publishing.

Sprint 44 builds that neutral foundation before any Telegram, VK, email, or other platform adapter is trusted.

## Goal

Add a platform-neutral publishing queue with durable job records, audit events, retry controls, and manual fallback controls, while keeping manual publication evidence compatible with the queue.

## Non-Goals

- No external platform API calls.
- No background scheduler or worker loop.
- No credential management.
- No automatic metric collection.
- No claim that a queued item has been posted externally.

## Product Behavior

An operator can open a publication detail page and:

1. Put an `approved` or `scheduled` publication into the publishing queue.
2. See the latest queue status, planned send time, attempts, retry state, and error message.
3. Retry a failed or manually-fallbacked queue item.
4. Mark a queue item as manual fallback with a reason when automation should not continue.
5. Read a short audit history for the latest queue item.

The existing manual publish fact remains the source of truth for "this post is actually live". Queue success in later sprints can update publication evidence, but Sprint 44 does not do that.

## Data Model

Add `cf_publishing_queue_item`:

- `id`
- `publication_id`
- `platform_id`
- `status`: `queued`, `processing`, `succeeded`, `failed`, `manual_fallback`, `cancelled`
- `scheduled_for`
- `requested_by_id`
- `attempts`
- `max_attempts`
- `last_attempt_at`
- `next_retry_at`
- `completed_at`
- `error_message`
- `manual_fallback_reason`
- `payload`
- `provider_response`
- `created_at`
- `updated_at`

Add `cf_publishing_queue_event`:

- `id`
- `queue_item_id`
- `publication_id`
- `actor_id`
- `event_type`: `queued`, `started`, `succeeded`, `failed`, `retry_requested`, `manual_fallback`, `cancelled`
- `message`
- `payload`
- `created_at`

The queue item payload stores a snapshot of the publication title, body, media refs, UTM, version number, scheduled time, and status at enqueue time. Publication records remain the editable source of truth; the snapshot is for audit and later platform workers.

## Backend API

Add routes under `/api/content-factory`:

- `GET /publishing-queue`
- `POST /publications/{publication_id}/publishing-queue`
- `GET /publications/{publication_id}/publishing-queue`
- `POST /publishing-queue/{queue_item_id}/retry`
- `POST /publishing-queue/{queue_item_id}/manual-fallback`
- `GET /publishing-queue/{queue_item_id}/events`

All routes require normal Content Factory access. Reference-table admin rights are not required because publishing operations are operational work, not taxonomy editing.

## Validation Rules

- Only `approved` and `scheduled` publications can be enqueued.
- A publication cannot have more than one active queue item in `queued` or `processing`; enqueue is idempotent and returns the active item.
- Retry is allowed only from `failed` or `manual_fallback`.
- Manual fallback is blocked for `succeeded` and `cancelled` queue items.
- Manual fallback reason is required and trimmed.

## Frontend UX

Add `ContentFactoryPublishingQueuePanel` to the publication detail sidebar near the existing workflow and operations panels.

The panel uses Russian operational labels:

- `Очередь публикации`
- `Поставить в очередь`
- `Повторить`
- `Ручной обход`
- `Журнал очереди`

The copy must be explicit that this is preparation for automated sending and audit, not proof of external publication.

## Testing

Backend:

- Model and migration source tests.
- Schema validation tests.
- Service tests for enqueue, idempotency, status validation, retry, failure metadata, and manual fallback.
- API tests for route wiring, commit behavior, 404, and validation-to-400 behavior.

Frontend:

- Source guard test for new queue API methods, types, panel strings, and route wiring.
- TypeScript, lint, build, and full frontend test suite.

## Manual QA

Use an authenticated Content Factory user:

1. Open an approved or scheduled publication.
2. Put it into the queue.
3. Confirm the panel shows queue status, planned time, attempts, and audit event.
4. Confirm early draft publications explain that approval or scheduling is required first.
5. Confirm manual fallback records a reason and keeps manual publish fact controls available.
