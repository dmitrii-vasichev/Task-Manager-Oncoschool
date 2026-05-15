# Content Factory Sprint 18 Publication Operations Plan

**Goal:** Make each publication detail page operationally clear: planned vs. actually published, post link stored or missing, platform process, and metric evidence.

**Architecture:** Keep Sprint 18 frontend-only and reuse existing REST endpoints. Add pure helpers in `contentFactoryUtils`, then render a small operations panel that PATCHes the existing publication record.

**Design:** `docs/superpowers/specs/2026-05-14-content-factory-sprint-18-publication-ops-design.md`

## Files

- Modify `frontend/src/lib/contentFactoryUtils.ts`
- Modify `frontend/src/lib/contentFactoryUtils.test.ts`
- Create `frontend/src/components/content-factory/ContentFactoryPublicationOperationsPanel.tsx`
- Modify `frontend/src/app/content-factory/publications/[id]/page.tsx`
- Modify `frontend/src/components/content-factory/contentFactorySourceGuards.test.ts`

Note: `docs/PLAN.md`, `docs/STATUS.md`, and `docs/TEST_PLAN.md` currently contain pre-existing local edits for Telegram overdue report readability. Do not mix those hunks into Sprint 18 commits.

## Phase 1: Plan And Failing Tests

- [x] Create Sprint 18 design and implementation plan.
- [x] Add helper tests for platform capability normalization.
- [x] Add helper tests for publication operation summary.
- [x] Add source guards for the new panel and detail-page integration.
- [x] Run focused tests once and confirm they fail for missing helper/panel integration.

## Phase 2: Helpers

- [x] Add `getContentFactoryPlatformCapabilities`.
- [x] Support manual defaults and opt-in API flags.
- [x] Add `getContentFactoryPublicationOperations`.
- [x] Add Russian metric evidence labels.

## Phase 3: Operations Panel

- [x] Create `ContentFactoryPublicationOperationsPanel`.
- [x] Render publication fact, platform process, metric process, post link, and metric evidence.
- [x] Add a compact dialog to save publication fact, post URL, and post ID.
- [x] Integrate the panel into `/content-factory/publications/[id]`.

## Phase 4: Verification And Integration

- [x] Run focused frontend tests.
- [x] Run full frontend tests, typecheck, lint, and build.
- [x] Run `git diff --check`.
- [x] Commit, merge to `main`, and push.

Latest verification:

- `cd frontend && node --test --experimental-strip-types src/lib/contentFactoryUtils.test.ts src/components/content-factory/contentFactorySourceGuards.test.ts` passed: 70 tests.
- `cd frontend && npm test` passed: 161 tests.
- `cd frontend && npx tsc --noEmit` passed.
- `cd frontend && npm run lint` passed.
- `cd frontend && npm run build` passed.
- `git diff --check` passed.

## Validation Commands

```bash
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryUtils.test.ts src/components/content-factory/contentFactorySourceGuards.test.ts
cd frontend && npm test
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
cd frontend && npm run build
git diff --check
```
