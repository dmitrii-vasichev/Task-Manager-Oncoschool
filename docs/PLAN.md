# Task Filter Sheet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the tall inline task filter toolbar with a compact search row and responsive filter sheet.

**Architecture:** Keep the existing task API and filtering state shape, but move structured filter presentation into a sheet opened from the task board header. Extract active-filter counting, chip generation, reset, and removal into a small pure helper module so the visible state can be tested without a browser. Reuse the existing Radix/shadcn `Sheet`, `Select`, `Popover`, and `Button` primitives.

**Tech Stack:** Next.js 14, React 18, TypeScript, Tailwind CSS, Radix/shadcn UI primitives, lucide-react, Node built-in test runner.

---

## Source Documents

- Approved design spec: `docs/superpowers/specs/2026-05-06-task-filter-sheet-design.md`
- Current task board: `frontend/src/app/tasks/page.tsx`
- Current filter component: `frontend/src/components/tasks/TaskFilters.tsx`
- Current labels picker: `frontend/src/components/tasks/TaskLabelPicker.tsx`
- Current sheet primitive: `frontend/src/components/ui/sheet.tsx`
- Current select primitive: `frontend/src/components/ui/select.tsx`

## Scope Check

This is one frontend UI subsystem. It does not require backend changes, label API changes, saved views, role changes, or changes to task visibility rules.

## File Structure

- Create `frontend/src/components/tasks/taskFilterUtils.ts`: pure filter-state helpers and exported `TaskFilterValues`.
- Create `frontend/src/components/tasks/taskFilterUtils.test.ts`: Node tests for active counts, chip generation, label overflow, reset behavior, and individual chip removal.
- Create `frontend/src/hooks/useMediaQuery.ts`: small client hook to choose right-side sheet on desktop and bottom sheet on smaller screens.
- Modify `frontend/package.json`: include the new helper test in `npm test`.
- Modify `frontend/src/components/tasks/TaskLabelPicker.tsx`: add a select-like chevron option and compact label summary for filter usage.
- Modify `frontend/src/components/tasks/TaskFilters.tsx`: replace the inline grid with compact search/filter row, responsive sheet, ordered fields, active chips, reset behavior, and helper usage.
- Modify `docs/STATUS.md`: record implementation progress and validation commands after execution starts.

---

## Task 1: Pure Filter Helpers and Tests

**Files:**

- Create: `frontend/src/components/tasks/taskFilterUtils.ts`
- Create: `frontend/src/components/tasks/taskFilterUtils.test.ts`
- Modify: `frontend/package.json`

- [ ] **Step 1: Write the failing helper tests**

Create `frontend/src/components/tasks/taskFilterUtils.test.ts`:

```ts
import assert from "node:assert/strict";
import test from "node:test";

import {
  buildActiveTaskFilterChips,
  clearStructuredTaskFilters,
  countActiveStructuredTaskFilters,
  EMPTY_FILTERS,
  removeTaskFilterChip,
  type ActiveTaskFilterChip,
  type TaskFilterValues,
} from "./taskFilterUtils.ts";
import type { Department, TaskLabel, TeamMember } from "../../lib/types.ts";

function label(id: string, name: string): TaskLabel {
  return {
    id,
    name,
    slug: name.toLowerCase().replace(/\s+/g, "-"),
    color: "teal",
    created_by_id: null,
    is_archived: false,
    usage_count: 1,
    created_at: "2026-05-06T00:00:00Z",
    updated_at: "2026-05-06T00:00:00Z",
  };
}

const departments: Department[] = [
  {
    id: "dept-dev",
    name: "Разработка",
    description: null,
    head_id: null,
    color: null,
    sort_order: 1,
    is_active: true,
    created_at: "2026-05-06T00:00:00Z",
  },
];

const members: TeamMember[] = [
  {
    id: "member-1",
    telegram_id: null,
    telegram_username: null,
    full_name: "Иван Петров",
    name_variants: [],
    department_id: "dept-dev",
    extra_department_ids: [],
    position: null,
    email: null,
    birthday: null,
    avatar_url: null,
    role: "member",
    is_test: false,
    is_active: true,
    created_at: "2026-05-06T00:00:00Z",
    updated_at: "2026-05-06T00:00:00Z",
  },
];

function filters(overrides: Partial<TaskFilterValues>): TaskFilterValues {
  return { ...EMPTY_FILTERS, ...overrides };
}

test("countActiveStructuredTaskFilters excludes search and counts label selection as one group", () => {
  const value = filters({
    search: "landing",
    labels: [label("label-vk", "VK"), label("label-site", "Site")],
    department_id: "dept-dev",
    assignee_id: "member-1",
    priority: "high",
    source: "voice",
  });

  assert.equal(
    countActiveStructuredTaskFilters(value, { showDepartmentFilter: true }),
    5
  );
});

test("countActiveStructuredTaskFilters ignores hidden department filter", () => {
  const value = filters({
    department_id: "dept-dev",
    source: "web",
  });

  assert.equal(
    countActiveStructuredTaskFilters(value, { showDepartmentFilter: false }),
    1
  );
});

test("buildActiveTaskFilterChips shows two labels plus overflow before other filters", () => {
  const value = filters({
    labels: [
      label("label-vk", "VK"),
      label("label-site", "Site"),
      label("label-crm", "CRM"),
    ],
    department_id: "dept-dev",
    assignee_id: "member-1",
    priority: "urgent",
    source: "summary",
  });

  const chips = buildActiveTaskFilterChips({
    filters: value,
    departments,
    members,
    showDepartmentFilter: true,
  });

  assert.deepEqual(
    chips.map((chip) => chip.label),
    [
      "VK",
      "Site",
      "+1 меток",
      "Отдел: Разработка",
      "Исполнитель: Иван Петров",
      "Срочный",
      "Summary",
    ]
  );
});

test("clearStructuredTaskFilters preserves search and clears structured fields", () => {
  const value = filters({
    search: "landing",
    labels: [label("label-vk", "VK")],
    department_id: "dept-dev",
    created_by_id: "member-1",
    priority: "low",
    source: "text",
  });

  assert.deepEqual(clearStructuredTaskFilters(value), {
    ...EMPTY_FILTERS,
    search: "landing",
  });
});

test("removeTaskFilterChip removes a selected label without clearing other labels", () => {
  const value = filters({
    labels: [
      label("label-vk", "VK"),
      label("label-site", "Site"),
    ],
  });
  const chip: ActiveTaskFilterChip = {
    type: "label",
    key: "label:label-vk",
    label: "VK",
    labelId: "label-vk",
  };

  assert.deepEqual(
    removeTaskFilterChip(value, chip).labels.map((item) => item.id),
    ["label-site"]
  );
});
```

- [ ] **Step 2: Update the frontend test command**

Modify `frontend/package.json`:

```json
"test": "node --test --experimental-strip-types src/lib/dateUtils.test.ts src/components/tasks/taskFilterUtils.test.ts"
```

- [ ] **Step 3: Run the tests and confirm the new tests fail**

Run:

```bash
cd frontend && npm test
```

Expected: FAIL because `frontend/src/components/tasks/taskFilterUtils.ts` does not exist.

- [ ] **Step 4: Implement the helper module**

Create `frontend/src/components/tasks/taskFilterUtils.ts`:

```ts
import type {
  Department,
  TaskLabel,
  TaskPriority,
  TaskSource,
  TeamMember,
} from "../../lib/types.ts";
import { TASK_PRIORITY_LABELS, TASK_SOURCE_LABELS } from "../../lib/types.ts";

export interface TaskFilterValues {
  search: string;
  priority: string;
  source: string;
  department_id: string;
  assignee_id: string;
  created_by_id: string;
  labels: TaskLabel[];
}

export const EMPTY_FILTERS: TaskFilterValues = {
  search: "",
  priority: "",
  source: "",
  department_id: "",
  assignee_id: "",
  created_by_id: "",
  labels: [],
};

export type ActiveTaskFilterChip =
  | {
      type: "label";
      key: string;
      label: string;
      labelId: string;
    }
  | {
      type: "label-overflow";
      key: "labels-overflow";
      label: string;
    }
  | {
      type: "field";
      key: keyof Pick<
        TaskFilterValues,
        "priority" | "source" | "department_id" | "assignee_id" | "created_by_id"
      >;
      label: string;
    };

export function countActiveStructuredTaskFilters(
  filters: TaskFilterValues,
  { showDepartmentFilter }: { showDepartmentFilter: boolean }
) {
  let count = 0;
  if (filters.labels.length > 0) count += 1;
  if (showDepartmentFilter && filters.department_id) count += 1;
  if (filters.assignee_id || filters.created_by_id) count += 1;
  if (filters.priority) count += 1;
  if (filters.source) count += 1;
  return count;
}

export function clearStructuredTaskFilters(
  filters: TaskFilterValues
): TaskFilterValues {
  return {
    ...EMPTY_FILTERS,
    search: filters.search,
  };
}

export function removeTaskFilterChip(
  filters: TaskFilterValues,
  chip: ActiveTaskFilterChip
): TaskFilterValues {
  if (chip.type === "label") {
    return {
      ...filters,
      labels: filters.labels.filter((label) => label.id !== chip.labelId),
    };
  }

  if (chip.type === "label-overflow") {
    return filters;
  }

  return {
    ...filters,
    [chip.key]: "",
  };
}

export function buildActiveTaskFilterChips({
  filters,
  members,
  departments,
  showDepartmentFilter,
  maxVisibleLabels = 2,
}: {
  filters: TaskFilterValues;
  members: TeamMember[];
  departments: Department[];
  showDepartmentFilter: boolean;
  maxVisibleLabels?: number;
}): ActiveTaskFilterChip[] {
  const chips: ActiveTaskFilterChip[] = [];
  const visibleLabels = filters.labels.slice(0, maxVisibleLabels);
  const hiddenLabelCount = filters.labels.length - visibleLabels.length;

  visibleLabels.forEach((label) => {
    chips.push({
      type: "label",
      key: `label:${label.id}`,
      label: label.name,
      labelId: label.id,
    });
  });

  if (hiddenLabelCount > 0) {
    chips.push({
      type: "label-overflow",
      key: "labels-overflow",
      label: `+${hiddenLabelCount} меток`,
    });
  }

  if (showDepartmentFilter && filters.department_id) {
    const department = departments.find(
      (item) => item.id === filters.department_id
    );
    chips.push({
      type: "field",
      key: "department_id",
      label: `Отдел: ${department?.name || "—"}`,
    });
  }

  if (filters.assignee_id) {
    const member = members.find((item) => item.id === filters.assignee_id);
    chips.push({
      type: "field",
      key: "assignee_id",
      label:
        filters.assignee_id === "unassigned"
          ? "Исполнитель: Не назначен"
          : `Исполнитель: ${member?.full_name || "—"}`,
    });
  }

  if (filters.created_by_id) {
    const member = members.find((item) => item.id === filters.created_by_id);
    chips.push({
      type: "field",
      key: "created_by_id",
      label: `Автор: ${member?.full_name || "—"}`,
    });
  }

  if (filters.priority) {
    chips.push({
      type: "field",
      key: "priority",
      label: TASK_PRIORITY_LABELS[filters.priority as TaskPriority],
    });
  }

  if (filters.source) {
    chips.push({
      type: "field",
      key: "source",
      label: TASK_SOURCE_LABELS[filters.source as TaskSource],
    });
  }

  return chips;
}
```

- [ ] **Step 5: Run helper tests**

Run:

```bash
cd frontend && npm test
```

Expected: PASS.

- [ ] **Step 6: Commit Task 1**

Run:

```bash
git add frontend/package.json frontend/src/components/tasks/taskFilterUtils.ts frontend/src/components/tasks/taskFilterUtils.test.ts
git commit -m "test: cover task filter helper state"
```

---

## Task 2: Responsive Sheet Side Hook

**Files:**

- Create: `frontend/src/hooks/useMediaQuery.ts`

- [ ] **Step 1: Add the media-query hook**

Create `frontend/src/hooks/useMediaQuery.ts`:

```ts
"use client";

import { useEffect, useState } from "react";

export function useMediaQuery(query: string) {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const mediaQueryList = window.matchMedia(query);

    function updateMatches() {
      setMatches(mediaQueryList.matches);
    }

    updateMatches();
    mediaQueryList.addEventListener("change", updateMatches);

    return () => {
      mediaQueryList.removeEventListener("change", updateMatches);
    };
  }, [query]);

  return matches;
}
```

- [ ] **Step 2: Run TypeScript check**

Run:

```bash
cd frontend && npx tsc --noEmit
```

Expected: PASS.

- [ ] **Step 3: Commit Task 2**

Run:

```bash
git add frontend/src/hooks/useMediaQuery.ts
git commit -m "feat: add media query hook"
```

---

## Task 3: Unified Labels Picker Trigger

**Files:**

- Modify: `frontend/src/components/tasks/TaskLabelPicker.tsx`

- [ ] **Step 1: Add chevron and compact summary support**

Modify the import:

```ts
import { Check, ChevronDown, Loader2, Plus, Search, X } from "lucide-react";
```

Modify the function signature props:

```ts
export function TaskLabelPicker({
  value,
  onChange,
  disabled = false,
  maxVisible = 3,
  placeholder = "Метки",
  variant = "default",
  displayMode = "chips",
  triggerClassName,
  showChevron = false,
}: {
  value: TaskLabel[];
  onChange: (labels: TaskLabel[]) => void;
  disabled?: boolean;
  maxVisible?: number;
  placeholder?: string;
  variant?: TaskLabelPickerVariant;
  displayMode?: TaskLabelPickerDisplayMode;
  triggerClassName?: string;
  showChevron?: boolean;
}) {
```

Add this summary value after `canCreate`:

```ts
  const summaryText =
    value.length === 0
      ? placeholder
      : value.length === 1
        ? value[0].name
        : `${value[0].name} +${value.length - 1}`;
```

Replace the `Button` children inside `PopoverTrigger` with:

```tsx
          <span className="flex min-w-0 flex-1 items-center">
            {value.length && displayMode === "summary" ? (
              <span className="min-w-0 truncate text-foreground">
                {summaryText}
              </span>
            ) : value.length ? (
              <TaskLabelChips
                labels={value}
                maxVisible={maxVisible}
                className={cn(
                  "flex-nowrap overflow-hidden",
                  variant === "compact" ? "max-w-[220px]" : "w-full"
                )}
              />
            ) : (
              <span className="truncate text-muted-foreground">
                {placeholder}
              </span>
            )}
          </span>
          {showChevron && (
            <ChevronDown className="h-4 w-4 shrink-0 opacity-50" />
          )}
```

Update the `Button` className base so the optional chevron can align with the text:

```ts
            "h-auto min-w-0 justify-between gap-2",
```

- [ ] **Step 2: Run TypeScript check**

Run:

```bash
cd frontend && npx tsc --noEmit
```

Expected: PASS.

- [ ] **Step 3: Commit Task 3**

Run:

```bash
git add frontend/src/components/tasks/TaskLabelPicker.tsx
git commit -m "feat: align task label picker trigger"
```

---

## Task 4: Filter Sheet UI

**Files:**

- Modify: `frontend/src/components/tasks/TaskFilters.tsx`

- [ ] **Step 1: Replace local filter value exports with helper exports**

Remove the local `TaskFilterValues`, `EMPTY_FILTERS`, and `ActiveFilter` definitions from `TaskFilters.tsx`.

Update the React import:

```ts
import { useMemo, useState, type ReactNode } from "react";
```

Add these imports:

```ts
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import {
  buildActiveTaskFilterChips,
  clearStructuredTaskFilters,
  countActiveStructuredTaskFilters,
  removeTaskFilterChip,
  EMPTY_FILTERS,
  type ActiveTaskFilterChip,
  type TaskFilterValues,
} from "@/components/tasks/taskFilterUtils";
```

Add this export near the imports so existing consumers keep working:

```ts
export { EMPTY_FILTERS, type TaskFilterValues } from "@/components/tasks/taskFilterUtils";
```

- [ ] **Step 2: Replace expanded inline state with sheet state**

Replace:

```ts
  const [filtersExpanded, setFiltersExpanded] = useState(false);
  const desktopGridClass = showDepartmentFilter
    ? FILTER_GRID_WITH_DEPARTMENT
    : FILTER_GRID_WITHOUT_DEPARTMENT;
```

with:

```ts
  const [filterSheetOpen, setFilterSheetOpen] = useState(false);
  const isDesktopSheet = useMediaQuery("(min-width: 768px)");
```

Remove `FILTER_GRID_WITH_DEPARTMENT` and `FILTER_GRID_WITHOUT_DEPARTMENT`.

- [ ] **Step 3: Add active chip and reset helpers**

After `selectedMemberFilterValue`, add:

```ts
  const activeFilterCount = countActiveStructuredTaskFilters(filters, {
    showDepartmentFilter,
  });
  const activeFilterChips = buildActiveTaskFilterChips({
    filters,
    members,
    departments,
    showDepartmentFilter,
  });

  function resetStructuredFilters() {
    onFiltersChange(clearStructuredTaskFilters(filters));
  }

  function handleActiveChipClick(chip: ActiveTaskFilterChip) {
    if (chip.type === "label-overflow") {
      setFilterSheetOpen(true);
      return;
    }
    onFiltersChange(removeTaskFilterChip(filters, chip));
  }
```

Remove the old `activeFilters` array construction and `removeFilter` function.

- [ ] **Step 4: Add the reusable field wrapper**

Add this local component before `return`:

```tsx
  function FilterField({
    label,
    children,
  }: {
    label: string;
    children: ReactNode;
  }) {
    return (
      <div className="space-y-1.5">
        <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {label}
        </div>
        {children}
      </div>
    );
  }
```

- [ ] **Step 5: Replace the render output with compact row, chips, and sheet**

Replace the `return (...)` block in `TaskFilters.tsx` with:

```tsx
  return (
    <div className="flex-1 space-y-2">
      <div className="grid gap-2 sm:grid-cols-[minmax(280px,1fr)_auto]">
        <div className="relative group min-w-0">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary" />
          <Input
            placeholder="Найти задачу..."
            value={filters.search}
            onChange={(event) =>
              onFiltersChange({ ...filters, search: event.target.value })
            }
            className="h-10 w-full rounded-xl border-border/70 bg-card pl-9 pr-9 shadow-sm focus:border-primary/40"
          />
          {filters.search && (
            <button
              type="button"
              aria-label="Очистить поиск"
              onClick={() => onFiltersChange({ ...filters, search: "" })}
              className="absolute right-2.5 top-1/2 rounded-full p-0.5 text-muted-foreground hover:text-foreground -translate-y-1/2"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setFilterSheetOpen(true)}
          className="h-10 justify-center rounded-xl border-border/70 bg-card px-4 shadow-sm"
          aria-label={
            activeFilterCount > 0
              ? `Открыть фильтры, активных фильтров: ${activeFilterCount}`
              : "Открыть фильтры"
          }
        >
          <SlidersHorizontal className="h-4 w-4" />
          {activeFilterCount > 0
            ? `Фильтры · ${activeFilterCount}`
            : "Фильтры"}
        </Button>
      </div>

      {activeFilterChips.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 animate-in fade-in slide-in-from-top-1 duration-200">
          {activeFilterChips.map((chip) => (
            <button
              key={chip.key}
              type="button"
              onClick={() => handleActiveChipClick(chip)}
              className={cn(
                "inline-flex max-w-full items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors",
                chip.type === "label-overflow"
                  ? "border-border/70 bg-muted text-muted-foreground hover:bg-muted/80"
                  : "border-primary/20 bg-primary/10 text-primary hover:bg-primary/20"
              )}
            >
              <span className="truncate">{chip.label}</span>
              {chip.type !== "label-overflow" && (
                <X className="h-3 w-3 opacity-60" />
              )}
            </button>
          ))}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={resetStructuredFilters}
            className="h-7 rounded-full px-2 text-xs text-muted-foreground hover:text-foreground"
          >
            <X className="h-3.5 w-3.5" />
            Сбросить
          </Button>
        </div>
      )}

      <Sheet open={filterSheetOpen} onOpenChange={setFilterSheetOpen}>
        <SheetContent
          side={isDesktopSheet ? "right" : "bottom"}
          className={cn(
            "flex max-h-[85dvh] flex-col gap-0 overflow-hidden p-0",
            isDesktopSheet
              ? "h-full w-full sm:max-w-md"
              : "rounded-t-2xl"
          )}
        >
          <SheetHeader className="border-b border-border/60 px-5 py-4 text-left">
            <SheetTitle>Фильтры</SheetTitle>
            <SheetDescription>
              Настройте вид доски задач
            </SheetDescription>
          </SheetHeader>

          <div className="flex-1 space-y-4 overflow-y-auto px-5 py-5">
            <FilterField label="Метки">
              <TaskLabelPicker
                value={filters.labels}
                onChange={(labels) => onFiltersChange({ ...filters, labels })}
                maxVisible={1}
                placeholder="Все метки"
                displayMode="summary"
                triggerClassName={FILTER_CONTROL_CLASS}
                showChevron
              />
            </FilterField>

            {showDepartmentFilter && (
              <FilterField label="Отдел">
                <Select
                  value={filters.department_id || "all"}
                  onValueChange={(value) => {
                    const nextDepartmentId = value === "all" ? "" : value;
                    const shouldResetAssignee =
                      Boolean(nextDepartmentId) &&
                      Boolean(filters.assignee_id) &&
                      filters.assignee_id !== "unassigned" &&
                      !members.some(
                        (member) =>
                          member.id === filters.assignee_id &&
                          member.department_id === nextDepartmentId
                      );
                    const shouldResetAuthor =
                      Boolean(nextDepartmentId) &&
                      Boolean(filters.created_by_id) &&
                      !members.some(
                        (member) =>
                          member.id === filters.created_by_id &&
                          member.department_id === nextDepartmentId
                      );

                    onFiltersChange({
                      ...filters,
                      department_id: nextDepartmentId,
                      assignee_id: shouldResetAssignee ? "" : filters.assignee_id,
                      created_by_id: shouldResetAuthor ? "" : filters.created_by_id,
                    });
                  }}
                >
                  <SelectTrigger className={FILTER_CONTROL_CLASS}>
                    <SelectValue placeholder="Отдел" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Все отделы</SelectItem>
                    {departments.map((department) => (
                      <SelectItem key={department.id} value={department.id}>
                        {department.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </FilterField>
            )}

            <FilterField label="Участник">
              <Select
                value={selectedMemberFilterValue}
                onValueChange={handleMemberValueChange}
              >
                <SelectTrigger className={FILTER_CONTROL_CLASS}>
                  <SelectValue placeholder="Участник" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Все участники</SelectItem>
                  <SelectSeparator />
                  <SelectGroup>
                    <SelectLabel>Исполнитель</SelectLabel>
                    <SelectItem value="assignee:unassigned">
                      <span className="text-muted-foreground">Не назначен</span>
                    </SelectItem>
                    {memberOptions.map((member) => (
                      <SelectItem
                        key={`assignee:${member.id}`}
                        value={`assignee:${member.id}`}
                      >
                        <span className="flex items-center gap-2">
                          <UserAvatar
                            name={member.full_name}
                            avatarUrl={member.avatar_url}
                            size="sm"
                          />
                          <span className="truncate">{member.full_name}</span>
                        </span>
                      </SelectItem>
                    ))}
                  </SelectGroup>
                  <SelectSeparator />
                  <SelectGroup>
                    <SelectLabel>Автор</SelectLabel>
                    {memberOptions.map((member) => (
                      <SelectItem
                        key={`author:${member.id}`}
                        value={`author:${member.id}`}
                      >
                        <span className="flex items-center gap-2">
                          <UserAvatar
                            name={member.full_name}
                            avatarUrl={member.avatar_url}
                            size="sm"
                          />
                          <span className="truncate">{member.full_name}</span>
                        </span>
                      </SelectItem>
                    ))}
                  </SelectGroup>
                </SelectContent>
              </Select>
            </FilterField>

            <FilterField label="Приоритет">
              <Select
                value={filters.priority || "all"}
                onValueChange={(value) =>
                  onFiltersChange({
                    ...filters,
                    priority: value === "all" ? "" : value,
                  })
                }
              >
                <SelectTrigger className={FILTER_CONTROL_CLASS}>
                  <SelectValue placeholder="Приоритет" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Все приоритеты</SelectItem>
                  {(Object.keys(TASK_PRIORITY_LABELS) as TaskPriority[]).map(
                    (priority) => (
                      <SelectItem key={priority} value={priority}>
                        <span className="flex items-center gap-2">
                          <span
                            className={`h-2 w-2 rounded-full ${PRIORITY_DOT_COLORS[priority]}`}
                          />
                          {TASK_PRIORITY_LABELS[priority]}
                        </span>
                      </SelectItem>
                    )
                  )}
                </SelectContent>
              </Select>
            </FilterField>

            <FilterField label="Источник">
              <Select
                value={filters.source || "all"}
                onValueChange={(value) =>
                  onFiltersChange({
                    ...filters,
                    source: value === "all" ? "" : value,
                  })
                }
              >
                <SelectTrigger className={FILTER_CONTROL_CLASS}>
                  <SelectValue placeholder="Источник" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Все источники</SelectItem>
                  {(Object.keys(TASK_SOURCE_LABELS) as TaskSource[]).map(
                    (source) => (
                      <SelectItem key={source} value={source}>
                        <span className="flex items-center gap-2">
                          <span className="text-xs">{SOURCE_ICONS[source]}</span>
                          {TASK_SOURCE_LABELS[source]}
                        </span>
                      </SelectItem>
                    )
                  )}
                </SelectContent>
              </Select>
            </FilterField>
          </div>

          <SheetFooter className="gap-2 border-t border-border/60 px-5 py-4 sm:space-x-0">
            <Button
              type="button"
              variant="outline"
              onClick={resetStructuredFilters}
              className="rounded-xl"
            >
              Сбросить
            </Button>
            <SheetClose asChild>
              <Button type="button" className="rounded-xl">
                Готово
              </Button>
            </SheetClose>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </div>
  );
```

- [ ] **Step 6: Remove unused imports and constants**

After the render replacement, remove unused `ChevronDown`, the old grid constants, and any old active-filter types that TypeScript reports.

- [ ] **Step 7: Run frontend checks**

Run:

```bash
cd frontend && npm test
cd frontend && npx tsc --noEmit
```

Expected: both commands PASS.

- [ ] **Step 8: Commit Task 4**

Run:

```bash
git add frontend/src/components/tasks/TaskFilters.tsx
git commit -m "feat: move task filters into sheet"
```

---

## Task 5: Manual UI Verification

**Files:**

- Modify: `docs/STATUS.md`

- [ ] **Step 1: Start the frontend dev server**

Run:

```bash
cd frontend && npm run dev -- --hostname 127.0.0.1 --port 3001
```

Expected: Next.js starts on `http://127.0.0.1:3001`.

- [ ] **Step 2: Verify desktop behavior**

Open `http://127.0.0.1:3001/tasks` in the in-app browser or Playwright.

Verify:

- default header shows search, `Фильтры`, and `Новая задача`;
- no active chip row appears when structured filters are empty;
- `Фильтры` opens a right-side sheet at desktop width;
- sheet order is labels, department, participant, priority, source;
- labels trigger has the same height, border, radius, background, and chevron as the other filter triggers;
- selecting one label creates one removable label chip;
- selecting three labels shows two label chips plus `+1 меток`;
- clicking a visible label chip removes only that label;
- clicking overflow opens the sheet;
- `Сбросить` clears structured filters and keeps the search text;
- `Готово` closes the sheet without changing active filters.

- [ ] **Step 3: Verify mobile behavior**

Set the browser viewport to a mobile width such as `390x844`.

Verify:

- search and filter button remain usable without text overlap;
- `Фильтры` opens a bottom sheet;
- bottom sheet content scrolls if needed;
- all controls fit within the sheet width;
- create button does not overlap the filter row.

- [ ] **Step 4: Run production-oriented checks**

Run:

```bash
cd frontend && npm test
cd frontend && npx tsc --noEmit
cd frontend && npm run build
```

Expected: all commands PASS.

- [ ] **Step 5: Update status**

Append this entry to `docs/STATUS.md` after verification:

```md
## Task Filter Sheet

- Current phase: implemented and verified
- Spec: `docs/superpowers/specs/2026-05-06-task-filter-sheet-design.md`
- Plan: `docs/PLAN.md`
- Latest verification:
  - Frontend helper tests pass.
  - Frontend TypeScript check passes.
  - Frontend production build passes.
  - Desktop task filter sheet manually verified.
  - Mobile bottom sheet manually verified.
```

- [ ] **Step 6: Commit Task 5**

Run:

```bash
git add docs/STATUS.md
git commit -m "docs: update task filter sheet status"
```

---

## Definition of Done

- The task board header no longer shows the full structured filter grid by default.
- Search remains visible and functional.
- `Фильтры · N` opens a responsive sheet.
- Desktop uses a right-side sheet.
- Mobile and tablet use a bottom sheet.
- The sheet field order is labels, department, participant, priority, source.
- Labels remain multi-select.
- Labels trigger visually matches the other filter triggers, including the chevron.
- Active label chips show individual labels with overflow after two labels.
- Reset clears structured filters and preserves search.
- `npm test`, `npx tsc --noEmit`, and `npm run build` pass from `frontend/`.
