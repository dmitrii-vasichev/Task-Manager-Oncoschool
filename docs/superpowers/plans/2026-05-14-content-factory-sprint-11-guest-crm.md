# Content Factory Sprint 11 Guest CRM Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a backend foundation for patient and guest story CRM records inside Content Factory.

**Architecture:** Follow the existing Content Factory backend pattern: SQLAlchemy model, Alembic migration, Pydantic schemas, focused service class, FastAPI router, and direct unit tests with mocked sessions. Keep the first API manual and CRUD-like so the frontend can build the workflow in the next sprint.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, Alembic, Pydantic v2, pytest, unittest `IsolatedAsyncioTestCase`.

---

## File Structure

- Modify `backend/app/db/models.py`: add `CFGuestStory`.
- Modify `backend/app/db/schemas.py`: add guest story `Literal` types and create/update/response schemas.
- Create `backend/alembic/versions/042_content_factory_guest_story.py`: create/drop `cf_guest_story`.
- Create `backend/app/services/content_factory/guest_story_service.py`: create/get/list/update methods.
- Create `backend/app/api/content_factory/guests.py`: list/create/get/update endpoints.
- Modify `backend/app/api/content_factory/__init__.py`: mount the guests router.
- Modify `backend/tests/test_content_factory_models.py`: assert the model exists and relationships configure.
- Modify `backend/tests/test_content_factory_schemas.py`: assert schema defaults and enum validation.
- Create `backend/tests/test_cf_guest_story_service.py`: service create/list/update tests.
- Create `backend/tests/test_content_factory_guest_stories_api.py`: endpoint behavior tests.
- Create `backend/tests/test_content_factory_guest_story_migration.py`: migration source guard.
- Modify `docs/PLAN.md`, `docs/STATUS.md`, `docs/TEST_PLAN.md`, and `docs/BACKLOG.md`: make Sprint 11 active and preserve Sprint 10 as completed context.

## Tasks

### Task 1: Write Failing Model And Schema Tests

**Files:**
- Modify: `backend/tests/test_content_factory_models.py`
- Modify: `backend/tests/test_content_factory_schemas.py`

- [ ] Add a model test:

```python
def test_cf_guest_story_exists(self):
    self.assertEqual(models.CFGuestStory.__tablename__, "cf_guest_story")
    self.assertTrue(hasattr(models.CFGuestStory, "status"))
    self.assertTrue(hasattr(models.CFGuestStory, "consent_status"))
    self.assertTrue(hasattr(models.CFGuestStory, "allowed_channels"))
```

- [ ] Add a schema-default test:

```python
def test_cf_guest_story_create_defaults(self):
    m = schemas.CFGuestStoryCreate(
        display_name="Patient story candidate",
        role="patient",
        owner_id=uuid.uuid4(),
    )
    self.assertEqual(m.status, "sourced")
    self.assertEqual(m.source, "manual")
    self.assertEqual(m.consent_status, "not_started")
    self.assertEqual(m.anonymity_level, "full_name")
    self.assertEqual(m.gift_status, "not_required")
    self.assertEqual(m.allowed_channels, [])
    self.assertEqual(m.sensitive_topics, [])
```

- [ ] Add an invalid-value test:

```python
def test_cf_guest_story_create_rejects_bad_status(self):
    with self.assertRaises(ValidationError):
        schemas.CFGuestStoryCreate(
            display_name="Patient story candidate",
            role="patient",
            owner_id=uuid.uuid4(),
            status="not_a_stage",
        )
```

- [ ] Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_content_factory_models.py tests/test_content_factory_schemas.py -q
```

Expected: fail because `CFGuestStory` and guest story schemas do not exist yet.

### Task 2: Implement Model, Schemas, And Migration

**Files:**
- Modify: `backend/app/db/models.py`
- Modify: `backend/app/db/schemas.py`
- Create: `backend/alembic/versions/042_content_factory_guest_story.py`

- [ ] Add guest story `Literal` types in `schemas.py`:

```python
CFGuestStoryRoleType = Literal["patient", "relative", "doctor", "volunteer", "partner", "other"]
CFGuestStorySourceType = Literal["manual", "open_call", "referral", "screening_form", "partner", "other"]
CFGuestStoryStatusType = Literal[
    "sourced", "applied", "editorial_screening", "shortlisted",
    "producer_call_scheduled", "producer_call_done",
    "medical_factcheck_needed", "doctor_approved",
    "consent_sent", "consent_signed", "scheduled",
    "prep_materials_sent", "live_or_recorded", "post_production",
    "published", "gift_sent", "follow_up_done",
    "maybe_later", "rejected", "archived",
]
CFGuestConsentStatusType = Literal["not_started", "sent", "signed", "declined", "revoked", "expired"]
CFGuestAnonymityLevelType = Literal["full_name", "first_name", "anonymous", "pseudonym"]
CFGuestGiftStatusType = Literal["not_required", "pending", "sent", "received"]
```

- [ ] Add `CFGuestStoryBase`, `CFGuestStoryCreate`, `CFGuestStoryUpdate`, and `CFGuestStoryResponse`.
- [ ] Add `CFGuestStory` with the fields from the design doc.
- [ ] Add Alembic revision `042_content_factory_guest_story` with `down_revision = "041"`.
- [ ] Run the model/schema tests again.

Expected: model and schema tests pass.

### Task 3: Write Failing Service Tests

**Files:**
- Create: `backend/tests/test_cf_guest_story_service.py`

- [ ] Add create, list-filter forwarding, and partial-update tests using `AsyncMock` sessions.
- [ ] Patch `GuestStoryService.get` in the update test the same way bundle service tests patch `BundleService.get`.
- [ ] Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_cf_guest_story_service.py -q
```

Expected: fail because `GuestStoryService` does not exist yet.

### Task 4: Implement Guest Story Service

**Files:**
- Create: `backend/app/services/content_factory/guest_story_service.py`

- [ ] Implement `create(session, payload)`.
- [ ] Implement `get(session, guest_story_id)`.
- [ ] Implement `list(session, *, status, owner_id, consent_status, bundle_id, publication_id, limit, offset)`.
- [ ] Implement `update(session, guest_story_id, payload)`.
- [ ] Sort list results by `stage_due_at.asc().nullslast()` and `created_at.desc()`.
- [ ] Run service tests.

Expected: service tests pass.

### Task 5: Write Failing API And Migration Tests

**Files:**
- Create: `backend/tests/test_content_factory_guest_stories_api.py`
- Create: `backend/tests/test_content_factory_guest_story_migration.py`

- [ ] Add API tests mirroring the existing retrospective API style: list, create commits, get 404, update 404, update commits.
- [ ] Add a migration source guard that imports or reads `042_content_factory_guest_story.py` and asserts it creates `cf_guest_story`, consent columns, indexes, and drops the table on downgrade.
- [ ] Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_content_factory_guest_stories_api.py tests/test_content_factory_guest_story_migration.py -q
```

Expected: fail because the router is not implemented or mounted yet.

### Task 6: Implement Router And Mount It

**Files:**
- Create: `backend/app/api/content_factory/guests.py`
- Modify: `backend/app/api/content_factory/__init__.py`

- [ ] Add `router = APIRouter(prefix="/guests", tags=["content-factory"])`.
- [ ] Add list/create/get/update endpoints using `require_cf_access`.
- [ ] Commit the session after create and update.
- [ ] Return `404` detail `История гостя не найдена` for missing reads and updates.
- [ ] Include the router in `content_factory_router`.
- [ ] Run API and migration tests.

Expected: API and migration tests pass.

### Task 7: Validate And Update Durable Docs

**Files:**
- Modify: `docs/PLAN.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/TEST_PLAN.md`
- Modify: `docs/BACKLOG.md`

- [ ] Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_content_factory_guest_stories_api.py tests/test_cf_guest_story_service.py tests/test_content_factory_models.py tests/test_content_factory_schemas.py tests/test_content_factory_guest_story_migration.py -q
git diff --check
```

Expected: all commands pass.

- [ ] Update `docs/STATUS.md` with implementation and verification results.
- [ ] Commit Sprint 11 implementation.
