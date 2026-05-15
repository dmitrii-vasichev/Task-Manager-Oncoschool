# Content Factory Sprint 28 Workflow Guardrails Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add backend and frontend guardrails so publication status changes follow the intended editorial workflow.

**Architecture:** Validate transitions in `PublicationService.update` before applying payload changes, then translate domain validation errors to HTTP 400 in the PATCH route. Expose publish-fact availability in the existing frontend operations summary and disable the dialog button for early workflow states.

**Tech Stack:** FastAPI, SQLAlchemy async service layer, Pydantic schemas, pytest/unittest, Next.js React components, Node source guard tests.

---

## File Map

- Modify `backend/app/services/content_factory/publication_service.py`: add transition map, schedule guard, and `PublicationWorkflowTransitionError`.
- Modify `backend/app/api/content_factory/publications.py`: catch workflow transition errors and return HTTP 400.
- Modify `backend/tests/test_cf_publication_service.py`: add service-level RED tests for invalid and valid transitions.
- Modify `backend/tests/test_content_factory_publications_api.py`: add API RED test for HTTP 400 on workflow validation errors.
- Modify `frontend/src/lib/contentFactoryUtils.ts`: add publish-fact availability fields to publication operations summary.
- Modify `frontend/src/lib/contentFactoryUtils.test.ts`: add utility RED tests for publish-fact availability.
- Modify `frontend/src/components/content-factory/ContentFactoryPublicationOperationsPanel.tsx`: disable publish fact button and show disabled reason.
- Modify `frontend/src/components/content-factory/contentFactorySourceGuards.test.ts`: guard operations panel wiring.
- Modify `docs/PLAN.md`, `docs/STATUS.md`, `docs/TEST_PLAN.md`, `docs/BACKLOG.md`: record Sprint 28 status and verification.

## Task 1: Backend RED Tests

- [ ] Add service tests for invalid `draft -> published`, invalid `approved -> scheduled` without date, and valid `approved -> scheduled` with same-payload date.
- [ ] Add API test that a `PublicationWorkflowTransitionError` becomes HTTP 400 and does not commit.
- [ ] Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest tests/test_cf_publication_service.py tests/test_content_factory_publications_api.py -q
```

Expected: FAIL because the exception and validation do not exist yet.

## Task 2: Backend Implementation

- [ ] Add `PublicationWorkflowTransitionError`.
- [ ] Add allowed transition map and helper validation functions.
- [ ] Call validation from `PublicationService.update` before mutating the publication.
- [ ] Catch the domain exception in the PATCH route and raise `HTTPException(status_code=400, detail=str(exc))`.
- [ ] Re-run the focused backend command.

Expected: PASS.

## Task 3: Frontend RED/GREEN

- [ ] Add utility assertions for `canSavePublishFact` and `publishFactDisabledReason`.
- [ ] Add source guards for disabled button wiring.
- [ ] Run:

```bash
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryUtils.test.ts src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected before implementation: FAIL.

- [ ] Add the operations summary fields and disable the publish fact button in the panel.
- [ ] Re-run the focused frontend command.

Expected: PASS.

## Task 4: Full Verification And Docs

- [ ] Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test OPENAI_API_KEY=test pytest tests/test_cf_publication_service.py tests/test_content_factory_publications_api.py -q
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryUtils.test.ts src/components/content-factory/contentFactorySourceGuards.test.ts
cd frontend && npm test
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
cd frontend && npm run build
git diff --check
```

Expected: PASS for every command.

- [ ] Update durable docs.
- [ ] Commit with `feat(cf): add publication workflow guardrails`.
- [ ] Merge to `main` with `--ff-only`.
- [ ] Push `main`.
