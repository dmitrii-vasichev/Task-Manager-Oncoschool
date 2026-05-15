# Content Factory Sprint 34 Variant Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add publication variant coverage so editors can see saved, missing, and stale channel adaptations at a glance.

**Architecture:** This is a frontend-only sprint. A pure helper in `contentFactoryUtils.ts` calculates coverage from the current publication version and saved variants; `ContentFactoryPublicationVariants` renders the result inside the existing adaptations panel.

**Tech Stack:** Next.js, React, TypeScript, Node test runner, existing Content Factory UI utilities.

---

## Files

- Modify `frontend/src/lib/contentFactoryUtils.ts`: add channel metadata and `getContentFactoryPublicationVariantCoverage`.
- Modify `frontend/src/lib/contentFactoryUtils.test.ts`: add helper tests.
- Modify `frontend/src/components/content-factory/ContentFactoryPublicationVariants.tsx`: render the coverage summary.
- Modify `frontend/src/components/content-factory/contentFactorySourceGuards.test.ts`: guard the new UI and helper wiring.
- Modify `docs/PLAN.md`, `docs/STATUS.md`, `docs/TEST_PLAN.md`, and `docs/BACKLOG.md`: record Sprint 34.

## Tasks

### Task 1: Write failing tests

- [ ] Add helper tests for full, missing, blank, and stale saved variants.
- [ ] Add source guards for `Готовность адаптаций`, `getContentFactoryPublicationVariantCoverage`, and `source_version_number`.
- [ ] Run focused frontend tests and confirm they fail because the helper/UI do not exist yet.

### Task 2: Implement coverage helper

- [ ] Export the six expected channel labels.
- [ ] Add `getContentFactoryPublicationVariantCoverage`.
- [ ] Count saved variants only when body text is nonblank.
- [ ] Count stale variants using `source_version_number < publication.version_number`.
- [ ] Return readable Russian labels and next action text.

### Task 3: Render coverage summary

- [ ] Compute coverage in `ContentFactoryPublicationVariants`.
- [ ] Add a compact summary block above channel tabs.
- [ ] Show saved, ready, missing, and stale state without changing existing save/copy behavior.

### Task 4: Verify

- [ ] Run focused frontend tests.
- [ ] Run the full frontend test suite.
- [ ] Run TypeScript, lint, build, and `git diff --check`.
- [ ] Update durable docs with final verification results.

## Validation Commands

```bash
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryUtils.test.ts src/components/content-factory/contentFactorySourceGuards.test.ts
cd frontend && npm test
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
cd frontend && npm run build
git diff --check
```
