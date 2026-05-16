# Content Factory Sprint 44 Publishing Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a platform-neutral publishing queue with durable jobs, audit events, retry controls, manual fallback, and a publication-detail panel.

**Architecture:** Add two backend tables and a focused queue service/API. Keep queue records separate from `cf_publication` so publication facts remain the source of truth for externally live posts. Add frontend types/API methods and a compact sidebar panel on publication detail pages.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, Alembic, Pydantic, pytest, Next.js App Router, React, TypeScript, Tailwind CSS, lucide-react, Node test runner.

---

### Task 1: Backend Queue Data Model

**Files:**
- Create: `backend/alembic/versions/046_cf_publishing_queue.py`
- Modify: `backend/app/db/models.py`
- Modify: `backend/app/db/schemas.py`
- Modify: `backend/tests/test_content_factory_models.py`
- Modify: `backend/tests/test_content_factory_schemas.py`
- Modify: `backend/tests/test_content_factory_guest_story_migration.py`

- [ ] **Step 1: Write failing model, schema, and migration tests**

Add assertions for `CFPublishingQueueItem`, `CFPublishingQueueEvent`, queue status/event literals, response schemas, manual fallback request validation, migration revision, tables, indexes, and downgrade.

- [ ] **Step 2: Run focused backend tests and verify RED**

Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest tests/test_content_factory_models.py tests/test_content_factory_schemas.py tests/test_content_factory_guest_story_migration.py -q
```

Expected: FAIL because the models, schemas, and migration do not exist.

- [ ] **Step 3: Add migration, models, and schemas**

Create the two queue tables, relationships, schema literals, response schemas, and manual fallback request schema.

- [ ] **Step 4: Run focused backend tests and verify GREEN**

Run the same focused backend command.

Expected: PASS.

### Task 2: Publishing Queue Service And API

**Files:**
- Create: `backend/app/services/content_factory/publishing_queue_service.py`
- Create: `backend/app/api/content_factory/publishing_queue.py`
- Modify: `backend/app/api/content_factory/__init__.py`
- Create: `backend/tests/test_cf_publishing_queue_service.py`
- Create: `backend/tests/test_content_factory_publishing_queue_api.py`

- [ ] **Step 1: Write failing service tests**

Cover enqueue snapshot creation, idempotent active enqueue, early-status rejection, retry from failed/manual fallback, manual fallback reason handling, and failure metadata.

- [ ] **Step 2: Run service tests and verify RED**

Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest tests/test_cf_publishing_queue_service.py -q
```

Expected: FAIL because the queue service does not exist.

- [ ] **Step 3: Implement queue service**

Add `PublishingQueueService` with `enqueue_publication`, `list_items`, `list_for_publication`, `list_events`, `retry_item`, `mark_manual_fallback`, and `record_attempt_failure`.

- [ ] **Step 4: Run service tests and verify GREEN**

Run the same service command.

Expected: PASS.

- [ ] **Step 5: Write failing API tests**

Cover enqueue, publication-specific queue list, global queue list filters, retry, manual fallback, events, 404, and validation errors.

- [ ] **Step 6: Run API tests and verify RED**

Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest tests/test_content_factory_publishing_queue_api.py -q
```

Expected: FAIL because the API module/routes are not wired.

- [ ] **Step 7: Implement API routes and router wiring**

Add queue endpoints under `/api/content-factory` and translate queue validation errors to HTTP 400.

- [ ] **Step 8: Run API tests and verify GREEN**

Run the same API command.

Expected: PASS.

### Task 3: Publication Detail Queue Panel

**Files:**
- Modify: `frontend/src/lib/types.ts`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/lib/contentFactoryUtils.ts`
- Create: `frontend/src/components/content-factory/ContentFactoryPublishingQueuePanel.tsx`
- Modify: `frontend/src/app/content-factory/publications/[id]/page.tsx`
- Modify: `frontend/src/components/content-factory/contentFactorySourceGuards.test.ts`

- [ ] **Step 1: Write failing frontend source guard**

Assert queue types/API methods exist, publication detail fetches queue items/events, and `ContentFactoryPublishingQueuePanel` exposes `Очередь публикации`, `Поставить в очередь`, `Повторить`, `Ручной обход`, and `Журнал очереди`.

- [ ] **Step 2: Run source guard and verify RED**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected: FAIL because queue frontend wiring does not exist.

- [ ] **Step 3: Add frontend types, API methods, labels, panel, and page wiring**

Load queue items and latest queue events on publication detail pages. Let users enqueue, retry, and mark manual fallback through the new API.

- [ ] **Step 4: Run source guard and verify GREEN**

Run the same source guard command.

Expected: PASS.

### Task 4: Durable Docs And Full Verification

**Files:**
- Modify: `docs/PLAN.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/TEST_PLAN.md`
- Modify: `docs/BACKLOG.md`

- [ ] **Step 1: Update durable docs**

Set Sprint 44 as the active plan, record queue design decisions, add validation commands, and move Sprint 44 out of the immediate backlog once verified.

- [ ] **Step 2: Run backend and frontend verification**

Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest tests/test_content_factory_models.py tests/test_content_factory_schemas.py tests/test_content_factory_guest_story_migration.py tests/test_cf_publishing_queue_service.py tests/test_content_factory_publishing_queue_api.py -q
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
cd frontend && npm test
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
cd frontend && npm run build
git diff --check
```

- [ ] **Step 3: Commit, merge, and push**

Use:

```bash
git add docs/PLAN.md docs/STATUS.md docs/TEST_PLAN.md docs/BACKLOG.md docs/superpowers/specs/2026-05-15-content-factory-sprint-44-publishing-queue-design.md docs/superpowers/plans/2026-05-15-content-factory-sprint-44-publishing-queue.md backend/alembic/versions/046_cf_publishing_queue.py backend/app/db/models.py backend/app/db/schemas.py backend/app/services/content_factory/publishing_queue_service.py backend/app/api/content_factory/publishing_queue.py backend/app/api/content_factory/__init__.py backend/tests/test_content_factory_models.py backend/tests/test_content_factory_schemas.py backend/tests/test_content_factory_guest_story_migration.py backend/tests/test_cf_publishing_queue_service.py backend/tests/test_content_factory_publishing_queue_api.py frontend/src/lib/types.ts frontend/src/lib/api.ts frontend/src/lib/contentFactoryUtils.ts frontend/src/components/content-factory/ContentFactoryPublishingQueuePanel.tsx frontend/src/app/content-factory/publications/[id]/page.tsx frontend/src/components/content-factory/contentFactorySourceGuards.test.ts
git commit -m "feat(cf): add publishing queue foundation"
git switch main
git merge --ff-only codex/content-factory-sprint-44-publishing-queue
git push origin main
```
