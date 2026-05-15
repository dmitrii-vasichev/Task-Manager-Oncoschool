# Content Factory Sprint 29 Metric Paste Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a frontend-only paste import flow for publication metric snapshots.

**Architecture:** Add pure parsing helpers in `contentFactoryUtils.ts`, cover them with Node tests, then add a dedicated import dialog that uses existing `api.recordCFMetric` sequentially for valid preview rows. Wire the dialog into the existing metric history panel without changing backend contracts.

**Tech Stack:** Next.js React components, existing UI primitives, TypeScript utility helpers, Node test runner, existing Content Factory REST API client.

---

## File Map

- Modify `frontend/src/lib/contentFactoryUtils.ts`: add metric import parser types, alias maps, normalization helpers, and `parseContentFactoryMetricImportRows`.
- Modify `frontend/src/lib/contentFactoryUtils.test.ts`: add RED tests for parsing valid rows, defaults, header skipping, and errors.
- Create `frontend/src/components/content-factory/ContentFactoryMetricImportDialog.tsx`: paste dialog with preview and sequential save.
- Modify `frontend/src/components/content-factory/ContentFactoryMetricHistory.tsx`: add `Импорт` action and render the new dialog.
- Modify `frontend/src/components/content-factory/contentFactorySourceGuards.test.ts`: guard component existence and API/parser wiring.
- Modify `docs/PLAN.md`, `docs/STATUS.md`, `docs/TEST_PLAN.md`, `docs/BACKLOG.md`: record Sprint 29 status and verification.

## Task 1: RED Tests

- [ ] Add helper tests in `frontend/src/lib/contentFactoryUtils.test.ts`.
- [ ] Add source guard assertions in `frontend/src/components/content-factory/contentFactorySourceGuards.test.ts`.
- [ ] Run:

```bash
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryUtils.test.ts src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected: FAIL because parser and import dialog do not exist yet.

## Task 2: Parser Implementation

- [ ] Add parser types and alias maps to `frontend/src/lib/contentFactoryUtils.ts`.
- [ ] Implement delimiter detection and header skipping.
- [ ] Normalize windows, sources, confidence, numeric values, and notes.
- [ ] Return valid and invalid preview rows without throwing.
- [ ] Re-run the focused frontend command.

Expected: helper parser tests pass; source guards still fail until the dialog exists.

## Task 3: Import Dialog And Wiring

- [ ] Create `ContentFactoryMetricImportDialog.tsx`.
- [ ] Add preview UI, invalid row display, save state, and sequential `api.recordCFMetric` calls.
- [ ] Wire `Импорт` button and dialog into `ContentFactoryMetricHistory.tsx`.
- [ ] Re-run the focused frontend command.

Expected: PASS.

## Task 4: Full Verification And Docs

- [ ] Run:

```bash
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryUtils.test.ts src/components/content-factory/contentFactorySourceGuards.test.ts
cd frontend && npm test
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
cd frontend && npm run build
git diff --check
```

Expected: PASS for every command.

- [ ] Update durable docs.
- [ ] Commit with `feat(cf): add metric paste import`.
- [ ] Merge to `main` with `--ff-only`.
- [ ] Push `main`.
