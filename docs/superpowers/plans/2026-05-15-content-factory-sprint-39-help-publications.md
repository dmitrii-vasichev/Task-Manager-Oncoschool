# Content Factory Sprint 39 Help For Publications Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add detailed practical help for calendar planning, publication records, channel adaptations, manual handoff, and readiness.

**Architecture:** Keep Sprint 39 frontend-only. Extend the existing static `/content-factory/help` route with structured arrays and rendered sections. Add a source-guard test to lock the key user-facing concepts.

**Tech Stack:** Next.js App Router, React, TypeScript, Tailwind CSS, lucide-react, Node test runner.

---

### Task 1: Guard Sprint 39 Help Content

**Files:**
- Modify: `frontend/src/components/content-factory/contentFactorySourceGuards.test.ts`

- [ ] **Step 1: Write the failing test**

Add this test near the existing help tests:

```ts
test("content factory help explains publication planning readiness and adaptations", () => {
  const source = readSource("app/content-factory/help/page.tsx");

  assert.match(source, /Планирование публикации: от календаря до готовности/);
  assert.match(source, /Календарь показывает рабочий план/);
  assert.match(source, /Карточка публикации собирает источник правды/);
  assert.match(source, /Адаптации показывают готовность каналов/);
  assert.match(source, /Чек-лист готовности помогает не пропустить шаг/);
  assert.match(source, /дата в календаре не означает автопубликацию/i);
  assert.match(source, /устаревш/i);
  assert.match(source, /скопировать готовые/i);
});
```

- [ ] **Step 2: Run focused test and verify RED**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected: FAIL because the help page does not yet contain the Sprint 39 publication planning section.

### Task 2: Add Publication Planning Help Sections

**Files:**
- Modify: `frontend/src/app/content-factory/help/page.tsx`

- [ ] **Step 1: Add structured content arrays**

Add arrays for:

- `PUBLICATION_PLANNING_HELP`
- `MANUAL_PUBLICATION_FLOW`
- `PUBLICATION_CONFUSION_NOTES`

- [ ] **Step 2: Render the section**

Render a new section after `Как начать без страха` and before `Разделы`. The section should include:

- a heading `Планирование публикации: от календаря до готовности`;
- four practical cards;
- a manual workflow list;
- common confusion notes.

- [ ] **Step 3: Run focused test and verify GREEN**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected: PASS.

### Task 3: Update Durable Docs

**Files:**
- Modify: `docs/PLAN.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/TEST_PLAN.md`
- Modify: `docs/BACKLOG.md`

- [ ] **Step 1: Update active plan**

Set `docs/PLAN.md` to Sprint 39 with design, plan, definition of done, and validation commands.

- [ ] **Step 2: Update status, test plan, and backlog**

Record RED/GREEN progress, add Sprint 39 manual QA, and remove Sprint 39 from the immediate backlog.

### Task 4: Full Verification And Integration

**Files:**
- No file changes expected after this task unless verification finds issues.

- [ ] **Step 1: Run full verification**

Run:

```bash
cd frontend && npm test
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
cd frontend && npm run build
git diff --check
```

- [ ] **Step 2: Commit, merge, and push**

Use:

```bash
git add docs/PLAN.md docs/STATUS.md docs/TEST_PLAN.md docs/BACKLOG.md docs/superpowers/specs/2026-05-15-content-factory-sprint-39-help-publications-design.md docs/superpowers/plans/2026-05-15-content-factory-sprint-39-help-publications.md frontend/src/app/content-factory/help/page.tsx frontend/src/components/content-factory/contentFactorySourceGuards.test.ts
git commit -m "feat(cf): add publication planning help"
git switch main
git merge --ff-only codex/content-factory-sprint-39-help-publications
git push origin main
```

