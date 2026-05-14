# Content Factory Sprint 4 Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the bundle and publication workspace so Content Factory users can move from dashboard/calendar visibility into campaign-level execution.

**Architecture:** Sprint 4 keeps the existing bundle-first model and REST API as the source of truth. The backend receives a narrow metadata-update contract needed by the editor, while the frontend adds typed API methods, pure workspace helpers, a bundle register, bundle detail workspace, publication editor, and version-history display.

**Tech Stack:** FastAPI, SQLAlchemy async services, Pydantic schemas, pytest, Next.js App Router, React, TypeScript, Tailwind, shadcn-style local UI primitives, lucide-react, Node test runner.

---

## File Structure

Backend:

- Modify `backend/app/db/schemas.py` so `CFBundleUpdate` can update `product_stream` and `owner_id`, and `CFPublicationUpdate` can update `platform_id`, `format_id`, `rubric_id`, `nosology_id`, and `responsible_id`.
- Modify `backend/tests/test_cf_bundle_service.py` to prove bundle owner and stream updates are persisted by the service.
- Modify `backend/tests/test_cf_publication_service.py` to prove publication metadata updates do not create a new body version.
- Modify `backend/tests/test_content_factory_bundles_api.py` and `backend/tests/test_content_factory_publications_api.py` only if the endpoint-level update forwarding needs explicit coverage beyond schema/service coverage.

Frontend:

- Modify `frontend/src/lib/types.ts` to keep frontend request types aligned with the backend update contract.
- Modify `frontend/src/lib/api.ts` to add `getCFBundle`, `createCFPublicationForBundle`, and `getCFPublicationVersions`.
- Modify `frontend/src/lib/contentFactoryUtils.ts` with bundle workspace helpers for params, count labels, schedule labels, relation lookup maps, and publication editing payload cleanup.
- Modify `frontend/src/lib/contentFactoryUtils.test.ts` with focused pure helper coverage.
- Modify `frontend/src/lib/contentFactoryApiSourceGuards.test.ts` with API method source guards.
- Create `frontend/src/components/content-factory/ContentFactoryBundleFilters.tsx` for bundle register filters.
- Create `frontend/src/components/content-factory/ContentFactoryBundleDialog.tsx` for create/edit bundle forms.
- Create `frontend/src/components/content-factory/ContentFactoryPublicationDialog.tsx` for create/edit publication forms.
- Create `frontend/src/components/content-factory/ContentFactoryPublicationVersionList.tsx` for version history display.
- Modify `frontend/src/components/content-factory/contentFactorySourceGuards.test.ts` with route/component source guards.
- Create `frontend/src/app/content-factory/bundles/page.tsx` for the bundle register.
- Create `frontend/src/app/content-factory/bundles/[id]/page.tsx` for the bundle detail workspace.
- Create `frontend/src/app/content-factory/publications/[id]/page.tsx` for the publication detail editor.
- Modify `frontend/src/components/layout/Header.tsx` and `frontend/src/components/layout/Sidebar.tsx` so bundle workspace routes have navigation metadata.

Docs:

- Update `docs/PLAN.md`, `docs/STATUS.md`, `docs/TEST_PLAN.md`, and `docs/BACKLOG.md` as Sprint 4 progresses.

---

## Task 1: Backend Update Contract And Frontend API Surface

**Files:**

- Modify: `backend/app/db/schemas.py`
- Modify: `backend/tests/test_cf_bundle_service.py`
- Modify: `backend/tests/test_cf_publication_service.py`
- Modify: `frontend/src/lib/types.ts`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/lib/contentFactoryApiSourceGuards.test.ts`

- [ ] **Step 1: Write failing bundle update contract test**

Append to `backend/tests/test_cf_bundle_service.py`:

```python
    async def test_update_bundle_owner_and_product_stream(self):
        session = AsyncMock()
        old_owner_id = uuid.uuid4()
        new_owner_id = uuid.uuid4()
        bundle = SimpleNamespace(
            id=uuid.uuid4(),
            name="Old",
            status="planning",
            product_stream="onco_school",
            owner_id=old_owner_id,
            brief=None,
        )
        BundleService.get = AsyncMock(return_value=bundle)

        result = await BundleService.update(
            session,
            bundle.id,
            CFBundleUpdate(product_stream="patient_live", owner_id=new_owner_id),
        )

        self.assertEqual(result.product_stream, "patient_live")
        self.assertEqual(result.owner_id, new_owner_id)
```

Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_cf_bundle_service.py::TestBundleService::test_update_bundle_owner_and_product_stream -q
```

Expected: fail because `CFBundleUpdate` does not accept `product_stream` or `owner_id`.

- [ ] **Step 2: Write failing publication metadata update contract test**

Append to `backend/tests/test_cf_publication_service.py`:

```python
    async def test_update_publication_metadata_without_body_version(self):
        session = AsyncMock()
        platform_id = uuid.uuid4()
        format_id = uuid.uuid4()
        rubric_id = uuid.uuid4()
        nosology_id = uuid.uuid4()
        responsible_id = uuid.uuid4()
        publication = SimpleNamespace(
            id=uuid.uuid4(),
            bundle_id=uuid.uuid4(),
            platform_id=uuid.uuid4(),
            format_id=uuid.uuid4(),
            rubric_id=None,
            nosology_id=None,
            responsible_id=uuid.uuid4(),
            body_text="stable body",
            version_number=1,
            status="draft",
            title="t",
        )
        PublicationService.get = AsyncMock(return_value=publication)

        result = await PublicationService.update(
            session,
            publication.id,
            CFPublicationUpdate(
                platform_id=platform_id,
                format_id=format_id,
                rubric_id=rubric_id,
                nosology_id=nosology_id,
                responsible_id=responsible_id,
            ),
            editor_id=responsible_id,
            approval_event="reviewed",
        )

        self.assertEqual(result.platform_id, platform_id)
        self.assertEqual(result.format_id, format_id)
        self.assertEqual(result.rubric_id, rubric_id)
        self.assertEqual(result.nosology_id, nosology_id)
        self.assertEqual(result.responsible_id, responsible_id)
        self.assertEqual(result.version_number, 1)
        session.add.assert_not_called()
```

Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_cf_publication_service.py::TestPublicationService::test_update_publication_metadata_without_body_version -q
```

Expected: fail because `CFPublicationUpdate` does not accept the metadata fields.

- [ ] **Step 3: Implement backend schema fields**

In `backend/app/db/schemas.py`, add to `CFBundleUpdate`:

```python
    product_stream: CFProductStreamType | None = None
    owner_id: uuid.UUID | None = None
```

Add to `CFPublicationUpdate`:

```python
    platform_id: uuid.UUID | None = None
    format_id: uuid.UUID | None = None
    rubric_id: uuid.UUID | None = None
    nosology_id: uuid.UUID | None = None
    responsible_id: uuid.UUID | None = None
```

No service change is required because both services already apply `payload.model_dump(exclude_unset=True)`.

- [ ] **Step 4: Verify backend update contract**

Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_cf_bundle_service.py tests/test_cf_publication_service.py -q
```

Expected: pass.

- [ ] **Step 5: Write failing frontend API source guard**

Add assertions to `frontend/src/lib/contentFactoryApiSourceGuards.test.ts`:

```typescript
assert.match(source, /async getCFBundle/);
assert.match(source, /async createCFPublicationForBundle/);
assert.match(source, /async getCFPublicationVersions/);
assert.match(source, /\/api\/content-factory\/bundles\/\$\{id\}/);
assert.match(source, /\/api\/content-factory\/bundles\/\$\{bundleId\}\/publications/);
assert.match(source, /\/api\/content-factory\/publications\/\$\{id\}\/versions/);
```

Run:

```bash
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryApiSourceGuards.test.ts
```

Expected: fail because the new API methods are missing.

- [ ] **Step 6: Implement frontend API methods and request fields**

In `frontend/src/lib/types.ts`, add the backend-aligned optional fields to `CFBundleUpdateRequest` and `CFPublicationUpdateRequest`.

In `frontend/src/lib/api.ts`, add:

```typescript
async getCFBundle(id: string): Promise<CFBundle> {
  return this.request<CFBundle>(`/api/content-factory/bundles/${id}`);
}

async createCFPublicationForBundle(
  bundleId: string,
  data: CFPublicationCreateRequest,
): Promise<CFPublication> {
  return this.request<CFPublication>(
    `/api/content-factory/bundles/${bundleId}/publications`,
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

async getCFPublicationVersions(id: string): Promise<CFPublicationVersion[]> {
  return this.request<CFPublicationVersion[]>(
    `/api/content-factory/publications/${id}/versions`,
  );
}
```

- [ ] **Step 7: Verify frontend API surface**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryApiSourceGuards.test.ts
```

Expected: pass.

---

## Task 2: Workspace Helpers And Source Guards

**Files:**

- Modify: `frontend/src/lib/contentFactoryUtils.ts`
- Modify: `frontend/src/lib/contentFactoryUtils.test.ts`
- Modify: `frontend/src/components/content-factory/contentFactorySourceGuards.test.ts`

- [ ] **Step 1: Write failing pure helper tests**

Add tests to `frontend/src/lib/contentFactoryUtils.test.ts` for:

```typescript
import {
  buildContentFactoryBundleParams,
  cleanContentFactoryPublicationUpdate,
  formatContentFactoryBundleCount,
  formatContentFactoryPublicationCount,
  getContentFactoryDisplayName,
} from "./contentFactoryUtils.ts";

test("buildContentFactoryBundleParams skips empty bundle filters", () => {
  assert.deepEqual(
    buildContentFactoryBundleParams({
      status: "all",
      product_stream: "",
      owner_id: "owner-1",
    }),
    { limit: "500", owner_id: "owner-1" },
  );
});

test("cleanContentFactoryPublicationUpdate trims strings and removes blank nullable fields", () => {
  assert.deepEqual(
    cleanContentFactoryPublicationUpdate({
      title: "  Reminder ",
      body_text: "",
      platform_post_url: "   ",
      platform_post_id: "vk-1",
      utm: { campaign: "may" },
    }),
    {
      title: "Reminder",
      body_text: null,
      platform_post_url: null,
      platform_post_id: "vk-1",
      utm: { campaign: "may" },
    },
  );
});

test("Content Factory count labels use Russian plural forms", () => {
  assert.equal(formatContentFactoryBundleCount(1), "1 bundle");
  assert.equal(formatContentFactoryBundleCount(2), "2 bundles");
  assert.equal(formatContentFactoryPublicationCount(5), "5 публикаций");
  assert.equal(formatContentFactoryPublicationCount(21), "21 публикация");
});

test("getContentFactoryDisplayName falls back to an id fragment", () => {
  assert.equal(
    getContentFactoryDisplayName("format-123456", []),
    "format-12",
  );
});
```

Run:

```bash
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryUtils.test.ts
```

Expected: fail because the helper functions are missing.

- [ ] **Step 2: Implement pure helpers**

Add exported helpers to `frontend/src/lib/contentFactoryUtils.ts`:

```typescript
export type ContentFactoryBundleFilterValues = {
  status: "all" | CFBundleStatus;
  product_stream: "" | CFProductStream;
  owner_id: string;
};

export function buildContentFactoryBundleParams(
  filters: ContentFactoryBundleFilterValues,
): Record<string, string> {
  const params: Record<string, string> = { limit: "500" };
  if (filters.status !== "all") params.status = filters.status;
  if (filters.product_stream) params.product_stream = filters.product_stream;
  if (filters.owner_id) params.owner_id = filters.owner_id;
  return params;
}
```

Also add:

- `formatContentFactoryBundleCount(count: number): string`
- `formatContentFactoryPublicationCount(count: number): string`
- `getContentFactoryDisplayName(id: string | null | undefined, records: Array<{ id: string; display_name?: string; full_name?: string; name?: string }>): string`
- `cleanContentFactoryPublicationUpdate(payload: CFPublicationUpdateRequest): CFPublicationUpdateRequest`

The cleanup helper must trim string fields and convert blank optional text fields to `null` for `title`, `body_text`, `platform_post_url`, `platform_post_id`, and `cancelled_reason`.

- [ ] **Step 3: Verify helper tests**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryUtils.test.ts
```

Expected: pass.

- [ ] **Step 4: Write failing source guards for new workspace routes**

Add assertions to `frontend/src/components/content-factory/contentFactorySourceGuards.test.ts`:

```typescript
assert.match(readSource("app/content-factory/bundles/page.tsx"), /api\.getCFBundles/);
assert.match(readSource("app/content-factory/bundles/[id]/page.tsx"), /api\.getCFBundle/);
assert.match(readSource("app/content-factory/publications/[id]/page.tsx"), /api\.getCFPublicationVersions/);
assert.match(source, /\/content-factory\/bundles/);
```

Run:

```bash
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected: fail because the route files and navigation entry are missing.

---

## Task 3: Bundle Register

**Files:**

- Create: `frontend/src/components/content-factory/ContentFactoryBundleFilters.tsx`
- Create: `frontend/src/components/content-factory/ContentFactoryBundleDialog.tsx`
- Create: `frontend/src/app/content-factory/bundles/page.tsx`
- Modify: `frontend/src/components/layout/Sidebar.tsx`
- Modify: `frontend/src/components/layout/Header.tsx`

- [ ] **Step 1: Implement bundle filters**

Create `ContentFactoryBundleFilters.tsx` with status, product stream, owner, and reset controls. Use existing local `Select`, `Button`, `X` icon, `CF_BUNDLE_STATUSES`, `CF_BUNDLE_STATUS_LABELS`, and `CF_PRODUCT_STREAM_LABELS`.

- [ ] **Step 2: Implement create/edit bundle dialog**

Create `ContentFactoryBundleDialog.tsx` with fields:

- name
- product stream
- owner
- status
- event date
- funnel template
- brief
- source material refs as newline-separated strings

On submit, call `api.createCFBundle` when no bundle is provided and `api.updateCFBundle` when editing an existing bundle.

- [ ] **Step 3: Implement bundle register page**

Create `/content-factory/bundles` with:

- a compact operational header
- a `New bundle` button
- `ContentFactoryBundleFilters`
- bundle count label
- bundle rows linking to `/content-factory/bundles/{id}`
- owner, status, product stream, event date, brief preview, and publication count placeholder when publication counts are unavailable

Use `api.getCFBundles(buildContentFactoryBundleParams(filters))`, `api.getTeam()`, and `api.getCFFunnelTemplates()`.

- [ ] **Step 4: Add navigation metadata**

Add `/content-factory/bundles` to header route metadata and Content Factory navigation.

- [ ] **Step 5: Verify bundle register source guards**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected: pass for bundle register guards.

---

## Task 4: Bundle Detail Workspace

**Files:**

- Create: `frontend/src/app/content-factory/bundles/[id]/page.tsx`
- Reuse: `frontend/src/components/content-factory/ContentFactoryBundleDialog.tsx`
- Reuse: `frontend/src/components/content-factory/ContentFactoryPublicationDialog.tsx`

- [ ] **Step 1: Implement publication create dialog**

Create `ContentFactoryPublicationDialog.tsx` with fields:

- platform
- format
- rubric
- nosology
- responsible user
- title
- body
- status
- scheduled datetime
- media refs as newline-separated strings
- UTM as editable JSON

When creating, call `api.createCFPublicationForBundle(bundle.id, payload)` with `bundle_id` in the request body.

- [ ] **Step 2: Implement bundle detail page**

Create `/content-factory/bundles/[id]` with:

- back link to `/content-factory/bundles`
- bundle header with status badge and edit action
- brief, owner, product stream, event date, funnel template, and source materials
- publication list grouped by production status
- publication cards with title/body preview, platform, format, responsible user, scheduled date, status, and links to `/content-factory/publications/{id}`
- create publication action

Load `api.getCFBundle(id)`, `api.getCFPublicationsForBundle(id)`, `api.getTeam()`, platforms, formats, rubrics, nosologies, and funnel templates in parallel.

- [ ] **Step 3: Verify detail source guards**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected: pass for bundle detail guards.

---

## Task 5: Publication Editor And Version History

**Files:**

- Create: `frontend/src/components/content-factory/ContentFactoryPublicationVersionList.tsx`
- Create: `frontend/src/app/content-factory/publications/[id]/page.tsx`
- Reuse: `frontend/src/components/content-factory/ContentFactoryPublicationDialog.tsx`

- [ ] **Step 1: Implement version list component**

Create `ContentFactoryPublicationVersionList.tsx` with a compact list of `version_number`, `edited_at`, `approval_event`, editor display name, notes, and body preview.

- [ ] **Step 2: Implement publication detail editor**

Create `/content-factory/publications/[id]` with:

- back link to the parent bundle
- publication header with status badge and edit action
- editable fields through `ContentFactoryPublicationDialog`
- status, platform, format, rubric, nosology, responsible user, schedule, UTM, post URL, post ID, cancelled reason, media refs
- version-history display from `api.getCFPublicationVersions(id)`

On save, call `api.updateCFPublication(id, cleanContentFactoryPublicationUpdate(payload))` and refetch publication plus versions.

- [ ] **Step 3: Verify publication editor source guards**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected: pass for publication editor guards.

---

## Task 6: Full Verification And Docs

**Files:**

- Modify: `docs/PLAN.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/TEST_PLAN.md`
- Modify: `docs/BACKLOG.md`

- [ ] **Step 1: Run backend focused verification**

Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_cf_bundle_service.py tests/test_cf_publication_service.py tests/test_content_factory_bundles_api.py tests/test_content_factory_publications_api.py -q
```

Expected: pass.

- [ ] **Step 2: Run frontend focused verification**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryUtils.test.ts src/lib/contentFactoryApiSourceGuards.test.ts src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected: pass.

- [ ] **Step 3: Run full frontend checks**

Run:

```bash
cd frontend && npm test
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
cd frontend && npm run build
```

Expected: pass.

- [ ] **Step 4: Run repository hygiene**

Run:

```bash
git diff --check
```

Expected: pass.

- [ ] **Step 5: Update durable repo docs**

Update:

- `docs/PLAN.md` with Sprint 4 status, definition of done, and validation commands.
- `docs/STATUS.md` with progress, decisions, next actions, and verification results.
- `docs/TEST_PLAN.md` with automated and manual Sprint 4 checks.
- `docs/BACKLOG.md` so Sprint 5 becomes the next workstream after Sprint 4.

---

## Self-Review

- Spec coverage: Sprint 4 roadmap coverage is mapped to backend update contract, bundle register, bundle detail workspace, publication editor, status editing, and version history. Segment targeting, metrics, and retrospectives remain Sprint 5/6 scope.
- Placeholder scan: This plan contains no `TBD`, `TODO`, or unspecified "add tests" steps. Each test step includes command and expected result.
- Type consistency: The frontend update request fields match the backend schema additions, and route/API names use the existing `CF` prefix already established in Sprint 3.
