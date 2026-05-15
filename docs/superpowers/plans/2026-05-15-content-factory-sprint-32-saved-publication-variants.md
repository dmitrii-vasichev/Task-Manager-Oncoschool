# Content Factory Sprint 32 Saved Publication Variants Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add durable saved channel variants for Content Factory publications.

**Architecture:** Add a small backend aggregate under publications: one saved variant per publication/channel. Keep Sprint 31 deterministic drafts as defaults, then let the frontend editor upsert saved channel text through the new API.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, Alembic, Pydantic, PostgreSQL JSONB/UUID conventions, Next.js App Router, React, TypeScript, Tailwind, Node test runner.

---

## File Structure

- Create `backend/alembic/versions/045_cf_publication_variants.py` for the table.
- Modify `backend/app/db/models.py` with `CFPublicationVariant` and `CFPublication.variants`.
- Modify `backend/app/db/schemas.py` with channel literal, response, and upsert schemas.
- Modify `backend/app/services/content_factory/publication_service.py` with list/upsert methods.
- Modify `backend/app/api/content_factory/publications.py` with variant endpoints.
- Modify backend tests for models, schemas, migration, service, and API.
- Modify `frontend/src/lib/types.ts` with variant types.
- Modify `frontend/src/lib/api.ts` with variant API methods.
- Modify `frontend/src/app/content-factory/publications/[id]/page.tsx` to load variants.
- Modify `frontend/src/components/content-factory/ContentFactoryPublicationVariants.tsx` into an editable saved-variant panel.
- Modify frontend source guard tests.
- Update `docs/PLAN.md`, `docs/STATUS.md`, `docs/TEST_PLAN.md`, and `docs/BACKLOG.md`.

## Task 1: Backend RED Tests

- [x] Add failing model, schema, migration, service, and API tests for saved publication variants.
- [x] Run focused backend tests and confirm RED because `CFPublicationVariant` and variant endpoints are missing.

## Task 2: Backend Implementation

- [x] Add Alembic migration `045_cf_publication_variants`.
- [x] Add `CFPublicationVariant` model and relationship.
- [x] Add Pydantic schemas.
- [x] Add `PublicationService.list_variants` and `PublicationService.upsert_variant`.
- [x] Add `GET` and `PUT` variant endpoints.
- [x] Run focused backend tests and confirm GREEN.

## Task 3: Frontend RED Tests

- [x] Add failing API/source guards for variant types, client methods, route loading, and editable component behavior.
- [x] Run focused frontend source guard tests and confirm RED.

## Task 4: Frontend Implementation

- [x] Add frontend variant types and API methods.
- [x] Load variants on publication detail pages.
- [x] Pass variants and refresh callback into `ContentFactoryPublicationVariants`.
- [x] Update the adaptations panel with title/body/notes editors, save, copy, reset-to-draft, and saved-state labels.
- [x] Run focused frontend tests and confirm GREEN.

## Task 5: Verification And Docs

- [x] Run focused backend and frontend verification.
- [x] Run full frontend verification.
- [x] Update durable docs with verification results.
- [ ] Commit, merge to `main`, and push.
- [ ] Mark Sprint 32 as pushed in docs, commit, and push the final docs update.

## Self-Review

- Spec coverage: the plan covers database, backend service/API, frontend API/types, UI, tests, docs, and verification.
- Placeholder scan: no placeholder tasks remain.
- Type consistency: channel names match Sprint 31 variant keys.
