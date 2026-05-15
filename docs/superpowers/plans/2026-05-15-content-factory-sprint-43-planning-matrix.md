# Content Factory Sprint 43 Planning Matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a campaign-level matrix that shows expected channel publications, existing records, missing slots, and quick creation shortcuts.

**Architecture:** Keep the sprint frontend-only. Add pure planning-matrix helpers in `contentFactoryUtils`, render the matrix from the campaign detail page, and create missing publications through the existing `createCFPublicationForBundle` API.

**Tech Stack:** Next.js App Router, React, TypeScript, Tailwind CSS, lucide-react, Node test runner.

---

### Task 1: Planning Matrix Helpers

**Files:**
- Modify: `frontend/src/lib/contentFactoryUtils.ts`
- Modify: `frontend/src/lib/contentFactoryUtils.test.ts`

- [x] **Step 1: Write failing helper tests**

Add tests that call `buildContentFactoryPlanningMatrix` and `summarizeContentFactoryPlanningMatrix`.

- [x] **Step 2: Run focused helper tests and verify RED**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryUtils.test.ts
```

Expected: FAIL because `buildContentFactoryPlanningMatrix` does not exist.

- [x] **Step 3: Implement helper types and functions**

Add matrix cell, row, matrix, and summary types. Implement template parsing, platform/format resolution, schedule offset calculation, publication matching, invalid-slot warnings, extra publication detection, and summary counts.

- [x] **Step 4: Run focused helper tests and verify GREEN**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryUtils.test.ts
```

Expected: PASS.

### Task 2: Campaign Matrix UI

**Files:**
- Create: `frontend/src/components/content-factory/ContentFactoryPlanningMatrix.tsx`
- Modify: `frontend/src/app/content-factory/bundles/[id]/page.tsx`
- Modify: `frontend/src/components/content-factory/contentFactorySourceGuards.test.ts`

- [x] **Step 1: Write failing source guard**

Assert the bundle detail page uses `ContentFactoryPlanningMatrix`, builds/summarizes the matrix, calls `api.createCFPublicationForBundle`, stores planning UTM markers, and exposes user-facing matrix labels.

- [x] **Step 2: Run source guard and verify RED**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected: FAIL because the matrix component does not exist.

- [x] **Step 3: Build component and page wiring**

Create `ContentFactoryPlanningMatrix`, render it above the campaign publication list, show summary counters, warnings, existing publication links, missing cells, and extra publications. Add a quick-create handler on the bundle detail page.

- [x] **Step 4: Run source guard and verify GREEN**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected: PASS.

### Task 3: Durable Docs And Full Verification

**Files:**
- Modify: `docs/PLAN.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/TEST_PLAN.md`
- Modify: `docs/BACKLOG.md`

- [x] **Step 1: Update durable docs**

Set Sprint 43 as the active plan, record design decisions and focused verification, add manual QA, and remove Sprint 43 from the immediate backlog.

- [x] **Step 2: Run full verification**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryUtils.test.ts src/components/content-factory/contentFactorySourceGuards.test.ts
cd frontend && npm test
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
cd frontend && npm run build
git diff --check
```

- [x] **Step 3: Commit, merge, and push**

Use:

```bash
git add docs/PLAN.md docs/STATUS.md docs/TEST_PLAN.md docs/BACKLOG.md docs/superpowers/specs/2026-05-15-content-factory-sprint-43-planning-matrix-design.md docs/superpowers/plans/2026-05-15-content-factory-sprint-43-planning-matrix.md frontend/src/lib/contentFactoryUtils.ts frontend/src/lib/contentFactoryUtils.test.ts frontend/src/components/content-factory/ContentFactoryPlanningMatrix.tsx frontend/src/components/content-factory/contentFactorySourceGuards.test.ts frontend/src/app/content-factory/bundles/[id]/page.tsx
git commit -m "feat(cf): add campaign planning matrix"
git switch main
git merge --ff-only codex/content-factory-sprint-43-planning-matrix
git push origin main
```
