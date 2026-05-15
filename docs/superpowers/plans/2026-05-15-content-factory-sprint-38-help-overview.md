# Content Factory Sprint 38 Help Overview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand `/content-factory/help` into a detailed overview and operating-model help page.

**Architecture:** Keep the implementation frontend-only. Extend the existing static help route and protect expected content through the existing source-guard test file. No backend API, schema, or route changes are required.

**Tech Stack:** Next.js App Router, React, TypeScript, Tailwind CSS, lucide-react, Node test runner.

---

### Task 1: Guard The Expanded Help Structure

**Files:**
- Modify: `frontend/src/components/content-factory/contentFactorySourceGuards.test.ts`

- [ ] **Step 1: Write the failing test**

Add a source-guard test that expects the help page to contain the new onboarding sections:

```ts
test("content factory overview help explains operating model and automation boundaries", () => {
  const source = readSource("app/content-factory/help/page.tsx");

  assert.match(source, /Почему это сделано именно так/);
  assert.match(source, /Как работает операционная модель/);
  assert.match(source, /Что уже можно делать сейчас/);
  assert.match(source, /Что будет автоматизировано позже/);
  assert.match(source, /Как начать без страха/);
  assert.match(source, /Excel/);
  assert.match(source, /автопубликац/i);
  assert.match(source, /кампания -> публикации -> адаптации -> проверка -> публикация -> метрики -> выводы/);
});
```

- [ ] **Step 2: Run focused test and verify RED**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected: FAIL because the current help page does not contain the new section headings and lifecycle sentence.

### Task 2: Expand The Help Page

**Files:**
- Modify: `frontend/src/app/content-factory/help/page.tsx`

- [ ] **Step 1: Implement the help content**

Replace the short help content with richer static sections:

- Hero summary.
- Research basis.
- Operating-model lifecycle.
- Current manual/semi-automated capabilities.
- Planned automation boundaries.
- First safe path for new users.
- Section directory.
- Expanded glossary.

- [ ] **Step 2: Run focused test and verify GREEN**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected: PASS.

### Task 3: Update Durable Repo Docs

**Files:**
- Modify: `docs/PLAN.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/TEST_PLAN.md`
- Modify: `docs/BACKLOG.md`

- [ ] **Step 1: Update active plan and status**

Set the active plan to Sprint 38, record the design and implementation plan paths, and note the current verification results.

- [ ] **Step 2: Update test plan and backlog**

Add Sprint 38 validation and move the roadmap item from next work to completed/in-progress status.

### Task 4: Full Verification And Integration

**Files:**
- No file changes expected after this task unless verification finds issues.

- [ ] **Step 1: Run full frontend verification**

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
git add docs/PLAN.md docs/STATUS.md docs/TEST_PLAN.md docs/BACKLOG.md docs/superpowers/specs/2026-05-15-content-factory-sprint-38-help-overview-design.md docs/superpowers/plans/2026-05-15-content-factory-sprint-38-help-overview.md frontend/src/app/content-factory/help/page.tsx frontend/src/components/content-factory/contentFactorySourceGuards.test.ts
git commit -m "feat(cf): expand content factory overview help"
git switch main
git merge --ff-only codex/content-factory-sprint-38-help-overview
git push origin main
```

