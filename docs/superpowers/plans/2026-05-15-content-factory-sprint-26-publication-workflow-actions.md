# Content Factory Sprint 26 Publication Workflow Actions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add quick publication workflow status actions to the Content Factory publication detail page.

**Architecture:** Keep Sprint 26 frontend-only. Add a pure helper in `contentFactoryUtils.ts`, a focused sidebar panel component, and wire it into `/content-factory/publications/[id]` using the existing `api.updateCFPublication` endpoint.

**Tech Stack:** Next.js App Router, React client components, TypeScript, Node test runner, lucide-react, Tailwind CSS.

---

## File Map

- Modify `frontend/src/lib/contentFactoryUtils.ts`: add workflow action types and `getContentFactoryPublicationWorkflowActions`.
- Modify `frontend/src/lib/contentFactoryUtils.test.ts`: add RED tests for action mapping and disabled scheduling.
- Create `frontend/src/components/content-factory/ContentFactoryPublicationWorkflowActionsPanel.tsx`: render buttons and call `api.updateCFPublication`.
- Modify `frontend/src/app/content-factory/publications/[id]/page.tsx`: render the workflow actions panel in the sidebar.
- Modify `frontend/src/components/content-factory/contentFactorySourceGuards.test.ts`: guard route and panel wiring.
- Modify `docs/PLAN.md`, `docs/STATUS.md`, `docs/TEST_PLAN.md`, `docs/BACKLOG.md`: record Sprint 26 status and verification.

## Task 1: Helper Tests

**Files:**

- Modify: `frontend/src/lib/contentFactoryUtils.test.ts`

- [ ] **Step 1: Import `getContentFactoryPublicationWorkflowActions`**

Add it to the destructuring block near the publication operations helpers.

- [ ] **Step 2: Add RED test for action mapping**

```ts
test("publication workflow actions expose readable next status steps", () => {
  assert.deepEqual(
    getContentFactoryPublicationWorkflowActions({
      status: "needs_copy",
      scheduled_at: null,
    }).map((action) => [
      action.key,
      action.targetStatus,
      action.label,
      action.tone,
      action.disabled,
    ]),
    [
      ["send_to_design", "needs_design", "Передать на дизайн", "default", false],
      ["send_to_factcheck", "factcheck", "На фактчек", "primary", false],
      ["cancel", "cancelled", "Отменить", "danger", false],
    ],
  );
});
```

- [ ] **Step 3: Add RED test for schedule guard and terminal states**

```ts
test("publication workflow actions guard scheduling and published state", () => {
  const approvedWithoutDate = getContentFactoryPublicationWorkflowActions({
    status: "approved",
    scheduled_at: null,
  });

  assert.deepEqual(
    approvedWithoutDate.map((action) => [
      action.key,
      action.targetStatus,
      action.disabled,
      action.disabledReason,
    ]),
    [
      [
        "schedule",
        "scheduled",
        true,
        "Сначала укажите плановую дату",
      ],
      ["return_to_doctor", "doctor_review", false, null],
      ["cancel", "cancelled", false, null],
    ],
  );

  assert.equal(
    getContentFactoryPublicationWorkflowActions({
      status: "published",
      scheduled_at: "2026-05-20T10:00:00Z",
    }).length,
    0,
  );
});
```

- [ ] **Step 4: Verify RED**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryUtils.test.ts
```

Expected: FAIL because `getContentFactoryPublicationWorkflowActions` is not implemented.

## Task 2: Source Guard Tests

**Files:**

- Modify: `frontend/src/components/content-factory/contentFactorySourceGuards.test.ts`

- [ ] **Step 1: Strengthen publication detail source guards**

In `publication detail route exposes publication operations panel`, add:

```ts
  const workflowPanelSource = readSource(
    "components/content-factory/ContentFactoryPublicationWorkflowActionsPanel.tsx",
  );

  assert.match(source, /ContentFactoryPublicationWorkflowActionsPanel/);
  assert.match(workflowPanelSource, /Быстрые действия/);
  assert.match(workflowPanelSource, /getContentFactoryPublicationWorkflowActions/);
  assert.match(workflowPanelSource, /api\.updateCFPublication/);
  assert.match(workflowPanelSource, /targetStatus/);
  assert.match(workflowPanelSource, /Сначала укажите плановую дату/);
  assert.match(utilsSource, /ContentFactoryPublicationWorkflowAction/);
  assert.match(utilsSource, /getContentFactoryPublicationWorkflowActions/);
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected: FAIL because the new panel does not exist and the route is not wired yet.

## Task 3: Utility Implementation

**Files:**

- Modify: `frontend/src/lib/contentFactoryUtils.ts`

- [ ] **Step 1: Add action types near publication operations types**

```ts
export type ContentFactoryPublicationWorkflowActionTone =
  | "primary"
  | "default"
  | "warning"
  | "danger"
  | "muted";

export type ContentFactoryPublicationWorkflowAction = {
  key: string;
  targetStatus: CFPublicationStatus;
  label: string;
  description: string;
  tone: ContentFactoryPublicationWorkflowActionTone;
  disabled: boolean;
  disabledReason: string | null;
};
```

- [ ] **Step 2: Implement an internal `workflowAction` builder**

The builder should accept the same fields and default `disabled` to `false` and `disabledReason` to `null`.

- [ ] **Step 3: Implement `getContentFactoryPublicationWorkflowActions`**

Use the mapping from the design doc. For `approved`, set the `schedule` action disabled when `scheduled_at` is blank or invalid.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryUtils.test.ts
```

Expected: PASS.

## Task 4: Workflow Actions Panel

**Files:**

- Create: `frontend/src/components/content-factory/ContentFactoryPublicationWorkflowActionsPanel.tsx`
- Modify: `frontend/src/app/content-factory/publications/[id]/page.tsx`

- [ ] **Step 1: Create the panel component**

The component receives:

```ts
{
  publication: CFPublication;
  onSaved: () => void | Promise<void>;
}
```

It derives actions with `getContentFactoryPublicationWorkflowActions(publication)`.

- [ ] **Step 2: Add save handling**

When an enabled action is clicked:

```ts
await api.updateCFPublication(publication.id, { status: action.targetStatus });
await onSaved();
```

Show `toastSuccess("Статус публикации обновлён")` on success and existing error toast pattern on failure.

- [ ] **Step 3: Render empty state**

When there are no actions, show:

```tsx
<p>Для этого статуса быстрых действий нет. Факт выхода и метрики ведутся ниже.</p>
```

- [ ] **Step 4: Wire into publication detail page**

Import `ContentFactoryPublicationWorkflowActionsPanel` and render it in the sidebar before `ContentFactoryPublicationOperationsPanel`.

- [ ] **Step 5: Verify source guards GREEN**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected: PASS.

## Task 5: Full Verification And Docs

**Files:**

- Modify: `docs/PLAN.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/TEST_PLAN.md`
- Modify: `docs/BACKLOG.md`

- [ ] **Step 1: Run focused combined verification**

```bash
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryUtils.test.ts src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected: PASS.

- [ ] **Step 2: Run full frontend verification**

```bash
cd frontend && npm test
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
cd frontend && npm run build
git diff --check
```

Expected: PASS for every command.

- [ ] **Step 3: Update durable docs**

Make Sprint 26 the top active plan in `docs/PLAN.md`, add a top status entry in `docs/STATUS.md`, add automated/manual checks to `docs/TEST_PLAN.md`, and add manual QA to `docs/BACKLOG.md`.

- [ ] **Step 4: Commit, merge, and push**

```bash
git add docs frontend
git commit -m "feat(cf): add publication workflow actions"
git switch main
git merge --ff-only codex/content-factory-sprint-26-publication-workflow-actions
git push origin main
```

