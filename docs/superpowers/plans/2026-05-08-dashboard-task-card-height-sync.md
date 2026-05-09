# Dashboard Task Card Height Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Synchronize paired dashboard task card heights across the `Просрочено` and `Активные` desktop columns while preserving natural stacked cards on mobile.

**Architecture:** Keep the existing dashboard data flow, grouping helper, and independent group expansion state. Add a desktop-only synchronized renderer inside `DashboardTaskBlock` that lays overdue and active previews into one two-column grid by row, while the existing stacked group renderer remains the only visible layout below the desktop breakpoint. Stretch grid cells with CSS, not fixed card heights.

**Tech Stack:** Next.js 14, React state, TypeScript, Tailwind CSS, Node `node:test`.

---

## File Structure

- Modify `frontend/src/app/dashboardCompletedWeekCard.test.ts`: add source guards for desktop row synchronization, responsive stacked fallback, hidden alignment cells, and no fixed card height.
- Modify `frontend/src/app/page.tsx`: add full-height compact task links, typed visible task groups, reusable group heading/expand helpers, stacked group renderer, and desktop synchronized task-row renderer.
- Modify `docs/STATUS.md`: record implementation progress and verification results after code changes are complete.

No backend files change. No API, database, task sorting, or activity-card changes are needed.

---

### Task 1: Add Frontend Source Guards

**Files:**
- Modify: `frontend/src/app/dashboardCompletedWeekCard.test.ts`
- Test: `frontend/src/app/dashboardCompletedWeekCard.test.ts`

- [ ] **Step 1: Add the failing dashboard height-sync guard**

Append this test to `frontend/src/app/dashboardCompletedWeekCard.test.ts`:

```ts
test("dashboard task rows synchronize desktop card heights without fixed card heights", () => {
  const source = readSource("app/page.tsx");
  const item = source.match(
    /function TaskListItem[\s\S]*?\/\/ ────────────────────────────────────────────\n\/\/ Section header/,
  );
  const block = source.match(
    /function DashboardTaskBlock[\s\S]*?function DashboardActivityCard/,
  );
  const sync = source.match(
    /function DashboardSynchronizedTaskGroups[\s\S]*?function DashboardTaskBlock/,
  );

  assert.ok(item, "dashboard task list item source should exist");
  assert.ok(block, "dashboard task block source should exist");
  assert.ok(sync, "synchronized dashboard task group source should exist");
  assert.match(source, /type DashboardVisibleTaskGroup = DashboardTaskGroup &/);
  assert.match(item[0], /relative flex h-full flex-col/);
  assert.match(block[0], /shouldSynchronizeTaskRows/);
  assert.match(block[0], /space-y-3 xl:hidden/);
  assert.match(sync[0], /synchronizedTaskRows/);
  assert.match(sync[0], /Array\.from\(\{\s*length:\s*Math\.max\(/);
  assert.match(sync[0], /hidden gap-x-4 gap-y-2 xl:grid xl:grid-cols-2/);
  assert.match(sync[0], /aria-hidden="true"/);
  assert.match(sync[0], /controlsId=\{`\$\{overdueGroup\.listId\} \$\{listId\}`\}/);
  assert.match(sync[0], /controlsId=\{`\$\{activeGroup\.listId\} \$\{listId\}`\}/);
  assert.doesNotMatch(item[0], /h-\[\d/);
  assert.doesNotMatch(sync[0], /h-\[\d/);
  assert.doesNotMatch(block[0], /h-\[\d/);
  assert.doesNotMatch(sync[0], /height:\s*\d/);
});
```

- [ ] **Step 2: Run the targeted test and verify it fails**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/app/dashboardCompletedWeekCard.test.ts
```

Expected: FAIL with an `AssertionError` because `DashboardVisibleTaskGroup`, `synchronizedTaskRows`, the `xl:hidden` stacked fallback, the desktop synchronized grid, and full-height compact task links are not implemented yet.

- [ ] **Step 3: Commit the failing test**

Run:

```bash
git add frontend/src/app/dashboardCompletedWeekCard.test.ts
git commit -m "test: guard dashboard task card height sync"
```

---

### Task 2: Implement Desktop Row Height Synchronization

**Files:**
- Modify: `frontend/src/app/page.tsx`
- Test: `frontend/src/app/dashboardCompletedWeekCard.test.ts`

- [ ] **Step 1: Add `Fragment` to the React import**

In `frontend/src/app/page.tsx`, replace:

```ts
import { useEffect, useMemo, useState } from "react";
```

with:

```ts
import { Fragment, useEffect, useMemo, useState } from "react";
```

- [ ] **Step 2: Let compact dashboard task links fill stretched grid cells**

In `TaskListItem`, replace the `Link` className:

```tsx
className={`relative block overflow-hidden rounded-xl p-3 transition-all duration-150 ${urgent ? "pl-4" : ""} ${borderClass}`}
```

with:

```tsx
className={`relative flex h-full flex-col overflow-hidden rounded-xl p-3 transition-all duration-150 ${urgent ? "pl-4" : ""} ${borderClass}`}
```

This keeps card height content-driven in normal stacks, but lets the link fill a taller synchronized desktop grid row.

- [ ] **Step 3: Add typed visible group and synchronized row shapes**

In `frontend/src/app/page.tsx`, after the existing `DashboardTaskGroup` type, add:

```ts
type DashboardVisibleTaskGroup = DashboardTaskGroup & {
  expanded: boolean;
  visibleTasks: Task[];
  hiddenCount: number;
  canExpand: boolean;
  listId: string;
};

type DashboardSynchronizedTaskRow = {
  rowIndex: number;
  overdueTask?: Task;
  activeTask?: Task;
};
```

- [ ] **Step 4: Add reusable dashboard task group helpers**

In `frontend/src/app/page.tsx`, after `DashboardEmptyState`, add:

```tsx
function DashboardTaskGroupHeading({
  group,
  headingId,
}: {
  group: DashboardVisibleTaskGroup;
  headingId: string;
}) {
  return (
    <div className="flex items-center justify-between gap-2">
      <h3
        id={headingId}
        className="text-xs font-medium text-muted-foreground"
      >
        {group.title}
      </h3>
      <span className="text-xs text-muted-foreground/70">
        {group.tasks.length}
      </span>
    </div>
  );
}

function DashboardTaskGroupExpandButton({
  group,
  controlsId,
  onExpandedChange,
}: {
  group: DashboardVisibleTaskGroup;
  controlsId: string;
  onExpandedChange: (groupKey: DashboardTaskGroupKey, expanded: boolean) => void;
}) {
  return (
    <button
      type="button"
      aria-expanded={group.expanded}
      aria-controls={controlsId}
      onClick={() => onExpandedChange(group.key, !group.expanded)}
      className="w-full rounded-xl border border-border/60 bg-background/70 px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:border-primary/30 hover:text-foreground"
    >
      {group.expanded ? "Свернуть" : `Показать ещё ${group.hiddenCount}`}
    </button>
  );
}

function DashboardStackedTaskGroups({
  id,
  visibleGroups,
  showAssignee,
  onGroupExpandedChange,
  className,
}: {
  id?: string;
  visibleGroups: DashboardVisibleTaskGroup[];
  showAssignee: boolean;
  onGroupExpandedChange: (
    groupKey: DashboardTaskGroupKey,
    expanded: boolean,
  ) => void;
  className: string;
}) {
  return (
    <div id={id} className={className}>
      {visibleGroups.map((group) => {
        const headingId = `${group.listId}-heading`;
        const taskGridClassName =
          visibleGroups.length === 1 ? "grid gap-3 md:grid-cols-2" : "space-y-2";

        return (
          <section
            key={group.key}
            aria-labelledby={headingId}
            className="space-y-2"
          >
            <DashboardTaskGroupHeading group={group} headingId={headingId} />
            <div id={group.listId} className={taskGridClassName}>
              {group.visibleTasks.map((task) => (
                <TaskListItem
                  key={task.id}
                  task={task}
                  variant={group.itemVariant}
                  showAssignee={showAssignee}
                />
              ))}
            </div>
            {group.canExpand && (
              <DashboardTaskGroupExpandButton
                group={group}
                controlsId={group.listId}
                onExpandedChange={onGroupExpandedChange}
              />
            )}
          </section>
        );
      })}
    </div>
  );
}

function DashboardSynchronizedTaskGroups({
  listId,
  overdueGroup,
  activeGroup,
  showAssignee,
  onGroupExpandedChange,
}: {
  listId: string;
  overdueGroup: DashboardVisibleTaskGroup;
  activeGroup: DashboardVisibleTaskGroup;
  showAssignee: boolean;
  onGroupExpandedChange: (
    groupKey: DashboardTaskGroupKey,
    expanded: boolean,
  ) => void;
}) {
  const synchronizedTaskRows: DashboardSynchronizedTaskRow[] = Array.from(
    {
      length: Math.max(
        overdueGroup.visibleTasks.length,
        activeGroup.visibleTasks.length,
      ),
    },
    (_, rowIndex) => ({
      rowIndex,
      overdueTask: overdueGroup.visibleTasks[rowIndex],
      activeTask: activeGroup.visibleTasks[rowIndex],
    }),
  );
  const overdueHeadingId = `${overdueGroup.listId}-synced-heading`;
  const activeHeadingId = `${activeGroup.listId}-synced-heading`;
  const hasExpandControls = overdueGroup.canExpand || activeGroup.canExpand;

  return (
    <div id={listId} className="hidden gap-x-4 gap-y-2 xl:grid xl:grid-cols-2">
      <DashboardTaskGroupHeading
        group={overdueGroup}
        headingId={overdueHeadingId}
      />
      <DashboardTaskGroupHeading
        group={activeGroup}
        headingId={activeHeadingId}
      />
      {synchronizedTaskRows.map(({ rowIndex, overdueTask, activeTask }) => (
        <Fragment key={rowIndex}>
          {overdueTask ? (
            <div className="h-full" aria-labelledby={overdueHeadingId}>
              <TaskListItem
                task={overdueTask}
                variant={overdueGroup.itemVariant}
                showAssignee={showAssignee}
              />
            </div>
          ) : (
            <div aria-hidden="true" />
          )}
          {activeTask ? (
            <div className="h-full" aria-labelledby={activeHeadingId}>
              <TaskListItem
                task={activeTask}
                variant={activeGroup.itemVariant}
                showAssignee={showAssignee}
              />
            </div>
          ) : (
            <div aria-hidden="true" />
          )}
        </Fragment>
      ))}
      {hasExpandControls && (
        <>
          <div>
            {overdueGroup.canExpand && (
              <DashboardTaskGroupExpandButton
                group={overdueGroup}
                controlsId={`${overdueGroup.listId} ${listId}`}
                onExpandedChange={onGroupExpandedChange}
              />
            )}
          </div>
          <div>
            {activeGroup.canExpand && (
              <DashboardTaskGroupExpandButton
                group={activeGroup}
                controlsId={`${activeGroup.listId} ${listId}`}
                onExpandedChange={onGroupExpandedChange}
              />
            )}
          </div>
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Replace the group rendering section inside `DashboardTaskBlock`**

Inside `DashboardTaskBlock`, replace the current `visibleGroups` and group layout constants:

```ts
const visibleGroups = groups
  ?.filter((group) => group.tasks.length > 0)
  .map((group) => {
    const groupExpanded = groupExpansion?.[group.key] ?? expanded;
    return {
      ...group,
      expanded: groupExpanded,
      visibleTasks: getDashboardTaskPreview(group.tasks, groupExpanded),
      hiddenCount: Math.max(
        0,
        group.tasks.length - DASHBOARD_TASK_PREVIEW_LIMIT,
      ),
      canExpand: group.tasks.length > DASHBOARD_TASK_PREVIEW_LIMIT,
      listId: `dashboard-${blockKey}-${group.key}-tasks`,
    };
  });
const hasVisibleGroups = Boolean(visibleGroups?.length);
const groupLayoutClassName =
  visibleGroups && visibleGroups.length > 1
    ? "grid gap-4 xl:grid-cols-2"
    : "space-y-3";
```

with:

```ts
const visibleGroups: DashboardVisibleTaskGroup[] | undefined = groups
  ?.filter((group) => group.tasks.length > 0)
  .map((group) => {
    const groupExpanded = groupExpansion?.[group.key] ?? expanded;
    return {
      ...group,
      expanded: groupExpanded,
      visibleTasks: getDashboardTaskPreview(group.tasks, groupExpanded),
      hiddenCount: Math.max(
        0,
        group.tasks.length - DASHBOARD_TASK_PREVIEW_LIMIT,
      ),
      canExpand: group.tasks.length > DASHBOARD_TASK_PREVIEW_LIMIT,
      listId: `dashboard-${blockKey}-${group.key}-tasks`,
    };
  });
const hasVisibleGroups = Boolean(visibleGroups?.length);
const overdueGroup = visibleGroups?.find((group) => group.key === "overdue");
const activeGroup = visibleGroups?.find((group) => group.key === "active");
const shouldSynchronizeTaskRows = Boolean(overdueGroup && activeGroup);
const groupLayoutClassName =
  visibleGroups && visibleGroups.length > 1
    ? "grid gap-4 xl:grid-cols-2"
    : "space-y-3";
```

Then replace the current grouped JSX branch:

```tsx
{hasVisibleGroups && visibleGroups ? (
  <div id={listId} className={groupLayoutClassName}>
    {visibleGroups.map((group) => {
      const headingId = `${group.listId}-heading`;
      const taskGridClassName =
        visibleGroups.length === 1
          ? "grid gap-3 md:grid-cols-2"
          : "space-y-2";

      return (
        <section
          key={group.key}
          aria-labelledby={headingId}
          className="space-y-2"
        >
          <div className="flex items-center justify-between gap-2">
            <h3
              id={headingId}
              className="text-xs font-medium text-muted-foreground"
            >
              {group.title}
            </h3>
            <span className="text-xs text-muted-foreground/70">
              {group.tasks.length}
            </span>
          </div>
          <div id={group.listId} className={taskGridClassName}>
            {group.visibleTasks.map((task) => (
              <TaskListItem
                key={task.id}
                task={task}
                variant={group.itemVariant}
                showAssignee={showAssignee}
              />
            ))}
          </div>
          {group.canExpand && (
            <button
              type="button"
              aria-expanded={group.expanded}
              aria-controls={group.listId}
              onClick={() =>
                setGroupExpanded(group.key, !group.expanded)
              }
              className="w-full rounded-xl border border-border/60 bg-background/70 px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:border-primary/30 hover:text-foreground"
            >
              {group.expanded
                ? "Свернуть"
                : `Показать ещё ${group.hiddenCount}`}
            </button>
          )}
        </section>
      );
    })}
  </div>
) : (
```

with:

```tsx
{hasVisibleGroups && visibleGroups ? (
  shouldSynchronizeTaskRows && overdueGroup && activeGroup ? (
    <>
      <DashboardStackedTaskGroups
        visibleGroups={visibleGroups}
        showAssignee={showAssignee}
        onGroupExpandedChange={setGroupExpanded}
        className="space-y-3 xl:hidden"
      />
      <DashboardSynchronizedTaskGroups
        listId={listId}
        overdueGroup={overdueGroup}
        activeGroup={activeGroup}
        showAssignee={showAssignee}
        onGroupExpandedChange={setGroupExpanded}
      />
    </>
  ) : (
    <DashboardStackedTaskGroups
      id={listId}
      visibleGroups={visibleGroups}
      showAssignee={showAssignee}
      onGroupExpandedChange={setGroupExpanded}
      className={groupLayoutClassName}
    />
  )
) : (
```

- [ ] **Step 6: Run the targeted source guard**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/app/dashboardCompletedWeekCard.test.ts
```

Expected: PASS. Existing Node warnings about `MODULE_TYPELESS_PACKAGE_JSON` may appear; they are not a failure.

- [ ] **Step 7: Run TypeScript**

Run:

```bash
cd frontend && npx tsc --noEmit
```

Expected: PASS with no TypeScript errors.

- [ ] **Step 8: Commit the implementation**

Run:

```bash
git add frontend/src/app/page.tsx
git commit -m "fix: synchronize dashboard task card heights"
```

---

### Task 3: Verify and Record Status

**Files:**
- Modify: `docs/STATUS.md`
- Test: frontend verification commands

- [ ] **Step 1: Run full frontend tests**

Run:

```bash
cd frontend && npm test
```

Expected: PASS.

- [ ] **Step 2: Run lint**

Run:

```bash
cd frontend && npm run lint
```

Expected: PASS with no ESLint errors.

- [ ] **Step 3: Run production build**

Run:

```bash
cd frontend && npm run build
```

Expected: PASS and compile the dashboard route successfully.

- [ ] **Step 4: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: PASS with no output.

- [ ] **Step 5: Update `docs/STATUS.md`**

Replace the existing `Dashboard Task Card Height Sync` section near the top of `docs/STATUS.md` with this section, after replacing the verification bullets with the exact command outcomes from Steps 1-4:

```md
## Dashboard Task Card Height Sync

- Current phase: implemented; automated verification passed
- Spec: `docs/superpowers/specs/2026-05-08-dashboard-task-card-height-sync-design.md`
- Plan: `docs/superpowers/plans/2026-05-08-dashboard-task-card-height-sync.md`
- Scope: dashboard task-block card height synchronization between overdue and active desktop columns
- Latest progress:
  - Approved row-level synchronization between `Просрочено` and `Активные`.
  - Kept the `Активность за 7 дней` card independent.
  - Added a desktop synchronized task grid and kept stacked natural-height groups below the desktop breakpoint.
  - Preserved independent group expansion controls.
- Key approved decisions:
  - Synchronize only task cards inside the dashboard task block.
  - Do not assign one fixed global height to all dashboard task cards.
  - Do not show visible empty alignment cells when one group has more tasks than the other.
  - Keep mobile layout stacked with overdue tasks first.
- Latest verification:
  - `cd frontend && node --test --experimental-strip-types src/app/dashboardCompletedWeekCard.test.ts` passed.
  - `cd frontend && npm test` passed.
  - `cd frontend && npx tsc --noEmit` passed.
  - `cd frontend && npm run lint` passed.
  - `cd frontend && npm run build` passed.
  - `git diff --check` passed.
```

- [ ] **Step 6: Commit verification docs**

Run:

```bash
git add docs/STATUS.md
git commit -m "docs: record dashboard task height sync verification"
```
