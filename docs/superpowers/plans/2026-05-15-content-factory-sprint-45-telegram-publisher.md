# Content Factory Sprint 45 Telegram Publisher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first real Content Factory publishing integration by sending due Telegram text publications through the existing application bot.

**Architecture:** Keep Sprint 44 queue records as the durable execution surface. Add a Telegram publisher that resolves an existing `telegram_notification_targets` destination, composes an escaped text message, sends through `aiogram.Bot`, and returns provider evidence. Add a queue processor/scheduler that moves due queue items through processing, success, retryable failure, or final failure while updating the related publication evidence.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, aiogram Bot, APScheduler, pytest, Next.js App Router, React, TypeScript, Tailwind CSS, Node test runner.

---

### Task 1: Backend Queue Processing Primitives

**Files:**
- Modify: `backend/app/services/content_factory/publishing_queue_service.py`
- Modify: `backend/tests/test_cf_publishing_queue_service.py`

- [ ] **Step 1: Write failing queue primitive tests**

Add tests named `test_list_due_items_filters_queued_due_and_retryable_rows`, `test_mark_processing_moves_item_and_records_started_event`, and `test_record_attempt_success_completes_item_and_records_event`.

The tests should assert `status`, `attempts`, `last_attempt_at`, `completed_at`, `provider_response`, and audit event type.

- [ ] **Step 2: Run queue primitive tests and verify RED**

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_cf_publishing_queue_service.py -q
```

Expected: FAIL because `list_due_items`, `mark_processing`, and `record_attempt_success` do not exist.

- [ ] **Step 3: Implement queue primitives**

Add methods:

```python
@staticmethod
async def list_due_items(session, *, now, limit=50) -> list[CFPublishingQueueItem]:
    raise NotImplementedError

@staticmethod
async def mark_processing(session, item, *, actor_id=None) -> CFPublishingQueueItem:
    raise NotImplementedError

@staticmethod
async def record_attempt_success(session, item, *, provider_response, actor_id=None) -> CFPublishingQueueItem:
    raise NotImplementedError
```

`list_due_items` must include queued rows whose `scheduled_for` is null or due and whose `next_retry_at` is null or due.

- [ ] **Step 4: Run queue primitive tests and verify GREEN**

Run the same pytest command.

Expected: PASS.

### Task 2: Telegram Publisher Service

**Files:**
- Create: `backend/app/services/content_factory/telegram_publisher_service.py`
- Create: `backend/tests/test_cf_telegram_publisher_service.py`

- [ ] **Step 1: Write failing Telegram publisher tests**

Cover tests named `test_builds_escaped_message_from_current_telegram_variant`, `test_resolves_explicit_utm_target_id`, `test_resolves_single_content_factory_target`, `test_rejects_missing_or_ambiguous_target`, `test_rejects_media_refs_before_sending`, and `test_send_message_returns_provider_evidence`.

The send test should use a fake bot with `send_message = AsyncMock(return_value=SimpleNamespace(message_id=321))`.

- [ ] **Step 2: Run Telegram publisher tests and verify RED**

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_cf_telegram_publisher_service.py -q
```

Expected: FAIL because `telegram_publisher_service` does not exist.

- [ ] **Step 3: Implement Telegram publisher**

Add:

```python
CONTENT_FACTORY_TARGET_TYPE = "content_factory"

class TelegramPublisherError(RuntimeError):
    """Raised when a Telegram publication cannot be sent safely."""

class TelegramPublisherService:
    async def publish(self, session, item, *, bot) -> dict[str, Any]:
        raise NotImplementedError
```

Implementation rules:

- Only platform code `telegram` is supported.
- Reject non-empty publication `media_refs`.
- Prefer a current `CFPublicationVariant(channel="telegram")`.
- HTML-escape title/body and send with `parse_mode="HTML"`.
- Resolve target by explicit UTM id or single active target with `content_factory` type.
- Return provider evidence with `platform`, `chat_id`, `thread_id`, `message_id`, and optional `post_url`.

- [ ] **Step 4: Run Telegram publisher tests and verify GREEN**

Run the same pytest command.

Expected: PASS.

### Task 3: Queue Processor, Scheduler, And Send-Now API

**Files:**
- Create: `backend/app/services/content_factory/publishing_scheduler_service.py`
- Modify: `backend/app/api/content_factory/publishing_queue.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_content_factory_publishing_queue_api.py`
- Create: `backend/tests/test_cf_publishing_scheduler_service.py`

- [ ] **Step 1: Write failing processor tests**

Cover tests named `test_send_now_marks_processing_sends_and_marks_success`, `test_send_now_records_failure_when_publisher_rejects`, and `test_process_due_queue_processes_each_due_item`.

The success test should assert publication evidence is updated to `published`, `actual_published_at`, and `platform_post_id`.

- [ ] **Step 2: Run processor tests and verify RED**

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_cf_publishing_scheduler_service.py -q
```

Expected: FAIL because `publishing_scheduler_service` does not exist.

- [ ] **Step 3: Implement processor and scheduler**

Add:

```python
class ContentFactoryPublishingSchedulerService:
    def start(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError

    async def process_due_queue(self) -> dict[str, int]:
        raise NotImplementedError

    async def send_now(self, session, queue_item_id, *, actor_id) -> CFPublishingQueueItem | None:
        raise NotImplementedError
```

`send_now` should call the Telegram publisher only for queued/failed/manual fallback items moved back to `queued` by existing retry behavior. It should commit only at API/scheduler boundaries.

- [ ] **Step 4: Write failing API send-now test**

Add to `backend/tests/test_content_factory_publishing_queue_api.py`:

Add tests named `test_send_publishing_queue_item_now_uses_scheduler` and `test_send_publishing_queue_item_now_returns_503_without_scheduler`.

- [ ] **Step 5: Run API tests and verify RED**

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_content_factory_publishing_queue_api.py -q
```

Expected: FAIL because the API route does not exist.

- [ ] **Step 6: Implement API route and main wiring**

Add route:

```python
POST /api/content-factory/publishing-queue/{queue_item_id}/send-now
```

Wire `ContentFactoryPublishingSchedulerService` in `backend/app/main.py` beside the existing broadcast scheduler.

- [ ] **Step 7: Run processor and API tests and verify GREEN**

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_cf_publishing_scheduler_service.py tests/test_content_factory_publishing_queue_api.py -q
```

Expected: PASS.

### Task 4: Frontend Queue Panel Send-Now Control

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/components/content-factory/ContentFactoryPublishingQueuePanel.tsx`
- Modify: `frontend/src/components/content-factory/contentFactorySourceGuards.test.ts`

- [ ] **Step 1: Write failing frontend source guard**

Assert:

```typescript
assert.match(apiSource, /sendCFPublishingQueueItemNow/);
assert.match(panelSource, /Отправить сейчас/);
assert.match(panelSource, /Telegram/);
```

- [ ] **Step 2: Run source guard and verify RED**

```bash
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected: FAIL because the API method and button do not exist.

- [ ] **Step 3: Add API method and panel action**

Add:

```typescript
async sendCFPublishingQueueItemNow(queueItemId: string): Promise<CFPublishingQueueItem> {
  return this.request<CFPublishingQueueItem>(`/api/content-factory/publishing-queue/${queueItemId}/send-now`, {
    method: "POST",
  });
}
```

Render `Отправить сейчас` only for the latest queued item.

- [ ] **Step 4: Run source guard and verify GREEN**

Run the same Node test command.

Expected: PASS.

### Task 5: Durable Docs And Full Verification

**Files:**
- Modify: `docs/PLAN.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/TEST_PLAN.md`
- Modify: `docs/BACKLOG.md`

- [ ] **Step 1: Update durable docs**

Set Sprint 45 as the active plan, record Telegram-only limitations, add validation commands, and move Sprint 45 out of the immediate backlog once verified.

- [ ] **Step 2: Run full verification**

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_cf_publishing_queue_service.py tests/test_cf_telegram_publisher_service.py tests/test_cf_publishing_scheduler_service.py tests/test_content_factory_publishing_queue_api.py -q
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest -q
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
cd frontend && npm test
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
cd frontend && npm run build
git diff --check
```

- [ ] **Step 3: Commit, merge, and push**

```bash
git add docs/PLAN.md docs/STATUS.md docs/TEST_PLAN.md docs/BACKLOG.md docs/superpowers/specs/2026-05-15-content-factory-sprint-45-telegram-publisher-design.md docs/superpowers/plans/2026-05-15-content-factory-sprint-45-telegram-publisher.md backend/app/services/content_factory/publishing_queue_service.py backend/app/services/content_factory/telegram_publisher_service.py backend/app/services/content_factory/publishing_scheduler_service.py backend/app/api/content_factory/publishing_queue.py backend/app/main.py backend/tests/test_cf_publishing_queue_service.py backend/tests/test_cf_telegram_publisher_service.py backend/tests/test_cf_publishing_scheduler_service.py backend/tests/test_content_factory_publishing_queue_api.py frontend/src/lib/api.ts frontend/src/components/content-factory/ContentFactoryPublishingQueuePanel.tsx frontend/src/components/content-factory/contentFactorySourceGuards.test.ts
git commit -m "feat(cf): publish queued telegram posts"
git switch main
git pull --ff-only origin main
git merge --ff-only codex/content-factory-sprint-45-telegram-publisher
git push origin main
```
