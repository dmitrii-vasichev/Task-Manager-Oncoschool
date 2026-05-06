"use client";

import { useMemo, useState } from "react";
import { Search, X, SlidersHorizontal, ChevronDown } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TaskLabelPicker } from "@/components/tasks/TaskLabelPicker";
import { UserAvatar } from "@/components/shared/UserAvatar";
import type { TaskPriority, TaskSource } from "@/lib/types";
import { TASK_PRIORITY_LABELS, TASK_SOURCE_LABELS } from "@/lib/types";
import type { Department, TaskLabel, TeamMember } from "@/lib/types";
import { cn } from "@/lib/utils";

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

const PRIORITY_DOT_COLORS: Record<string, string> = {
  urgent: "bg-priority-urgent-dot",
  high: "bg-priority-high-dot",
  medium: "bg-priority-medium-dot",
  low: "bg-priority-low-dot",
};

const SOURCE_ICONS: Record<string, string> = {
  text: "📝",
  voice: "🎤",
  summary: "📋",
  web: "🌐",
};

const FILTER_CONTROL_CLASS =
  "h-9 w-full rounded-lg border-border/70 bg-background/80 shadow-none hover:border-primary/30 data-[state=open]:border-primary/40 data-[state=open]:shadow-none";

const FILTER_GRID_WITH_DEPARTMENT =
  "min-[1680px]:grid-cols-[minmax(240px,1fr)_minmax(142px,0.58fr)_minmax(142px,0.58fr)_minmax(164px,0.68fr)_minmax(150px,0.6fr)_minmax(170px,0.74fr)]";

const FILTER_GRID_WITHOUT_DEPARTMENT =
  "min-[1500px]:grid-cols-[minmax(260px,1fr)_minmax(150px,0.65fr)_minmax(150px,0.65fr)_minmax(170px,0.72fr)_minmax(180px,0.78fr)]";

interface ActiveFilter {
  key: keyof TaskFilterValues;
  label: string;
}

interface TaskFiltersProps {
  filters: TaskFilterValues;
  onFiltersChange: (filters: TaskFilterValues) => void;
  members: TeamMember[];
  departments: Department[];
  showDepartmentFilter?: boolean;
}

export function TaskFilters({
  filters,
  onFiltersChange,
  members,
  departments,
  showDepartmentFilter = true,
}: TaskFiltersProps) {
  const [filtersExpanded, setFiltersExpanded] = useState(false);
  const desktopGridClass = showDepartmentFilter
    ? FILTER_GRID_WITH_DEPARTMENT
    : FILTER_GRID_WITHOUT_DEPARTMENT;
  const memberOptions = useMemo(
    () =>
      filters.department_id
        ? members.filter((m) => m.department_id === filters.department_id)
        : members,
    [filters.department_id, members]
  );
  const selectedMemberFilterValue = useMemo(() => {
    if (filters.created_by_id) return `author:${filters.created_by_id}`;
    if (filters.assignee_id === "unassigned") return "assignee:unassigned";
    if (filters.assignee_id) return `assignee:${filters.assignee_id}`;
    return "all";
  }, [filters.assignee_id, filters.created_by_id]);

  const activeFilters: ActiveFilter[] = [];
  if (filters.priority) {
    activeFilters.push({
      key: "priority",
      label: TASK_PRIORITY_LABELS[filters.priority as TaskPriority],
    });
  }
  if (filters.source) {
    activeFilters.push({
      key: "source",
      label: TASK_SOURCE_LABELS[filters.source as TaskSource],
    });
  }
  if (filters.labels.length > 0) {
    activeFilters.push({
      key: "labels",
      label:
        filters.labels.length === 1
          ? `Метка: ${filters.labels[0].name}`
          : `Метки: ${filters.labels.length}`,
    });
  }
  if (showDepartmentFilter && filters.department_id) {
    const department = departments.find((d) => d.id === filters.department_id);
    activeFilters.push({
      key: "department_id",
      label: department?.name || "Отдел",
    });
  }
  if (filters.assignee_id) {
    const member = members.find((m) => m.id === filters.assignee_id);
    activeFilters.push({
      key: "assignee_id",
      label:
        filters.assignee_id === "unassigned"
          ? "Исполнитель: Не назначен"
          : `Исполнитель: ${member?.full_name || "—"}`,
    });
  }
  if (filters.created_by_id) {
    const member = members.find((m) => m.id === filters.created_by_id);
    activeFilters.push({
      key: "created_by_id",
      label: `Автор: ${member?.full_name || "—"}`,
    });
  }

  function removeFilter(key: keyof TaskFilterValues) {
    onFiltersChange({
      ...filters,
      [key]: key === "labels" ? [] : "",
    });
  }

  function handleMemberValueChange(value: string) {
    if (value === "all") {
      onFiltersChange({
        ...filters,
        assignee_id: "",
        created_by_id: "",
      });
      return;
    }

    if (value === "assignee:unassigned") {
      onFiltersChange({
        ...filters,
        assignee_id: "unassigned",
        created_by_id: "",
      });
      return;
    }

    if (value.startsWith("assignee:")) {
      onFiltersChange({
        ...filters,
        assignee_id: value.slice("assignee:".length),
        created_by_id: "",
      });
      return;
    }

    onFiltersChange({
      ...filters,
      assignee_id: "",
      created_by_id: value.startsWith("author:")
        ? value.slice("author:".length)
        : "",
    });
  }

  return (
    <div className="flex-1 rounded-xl border border-border/70 bg-card/90 p-2.5 shadow-sm shadow-slate-200/50 dark:shadow-none">
      <div
        className={cn(
          "grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3",
          desktopGridClass
        )}
      >
        <div className="relative group sm:col-span-2 lg:col-span-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground group-focus-within:text-primary" />
          <Input
            placeholder="Найти задачу..."
            value={filters.search}
            onChange={(e) =>
              onFiltersChange({ ...filters, search: e.target.value })
            }
            className="h-9 w-full rounded-lg border-border/70 bg-background/80 pl-9 shadow-none focus:border-primary/40"
          />
          {filters.search && (
            <button
              type="button"
              aria-label="Очистить поиск"
              onClick={() => onFiltersChange({ ...filters, search: "" })}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground rounded-full p-0.5"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setFiltersExpanded(!filtersExpanded)}
          className="h-9 rounded-lg gap-1.5 border-border/70 bg-background/80 shadow-none sm:col-span-2 lg:hidden"
        >
          <SlidersHorizontal className="h-4 w-4" />
          Фильтры
          <ChevronDown
            className={`h-3.5 w-3.5 transition-transform ${filtersExpanded ? "rotate-180" : ""}`}
          />
        </Button>

        <div
          className={cn(
            "gap-2 sm:col-span-2 sm:grid-cols-2 lg:contents",
            filtersExpanded ? "grid lg:contents" : "hidden lg:contents"
          )}
        >
          <Select
            value={filters.priority || "all"}
            onValueChange={(v) =>
              onFiltersChange({ ...filters, priority: v === "all" ? "" : v })
            }
          >
            <SelectTrigger className={FILTER_CONTROL_CLASS}>
              <SelectValue placeholder="Приоритет" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Все приоритеты</SelectItem>
              {(Object.keys(TASK_PRIORITY_LABELS) as TaskPriority[]).map(
                (p) => (
                  <SelectItem key={p} value={p}>
                    <span className="flex items-center gap-2">
                      <span
                        className={`h-2 w-2 rounded-full ${PRIORITY_DOT_COLORS[p]}`}
                      />
                      {TASK_PRIORITY_LABELS[p]}
                    </span>
                  </SelectItem>
                )
              )}
            </SelectContent>
          </Select>

          {/* Source */}
          <Select
            value={filters.source || "all"}
            onValueChange={(v) =>
              onFiltersChange({ ...filters, source: v === "all" ? "" : v })
            }
          >
            <SelectTrigger className={FILTER_CONTROL_CLASS}>
              <SelectValue placeholder="Источник" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Все источники</SelectItem>
              {(Object.keys(TASK_SOURCE_LABELS) as TaskSource[]).map((s) => (
                <SelectItem key={s} value={s}>
                  <span className="flex items-center gap-2">
                    <span className="text-xs">{SOURCE_ICONS[s]}</span>
                    {TASK_SOURCE_LABELS[s]}
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="min-w-0">
            <TaskLabelPicker
              value={filters.labels}
              onChange={(labels) => onFiltersChange({ ...filters, labels })}
              maxVisible={1}
              placeholder="Все метки"
              displayMode="summary"
              triggerClassName={FILTER_CONTROL_CLASS}
            />
          </div>

          {showDepartmentFilter && (
            <Select
              value={filters.department_id || "all"}
              onValueChange={(v) => {
                const nextDepartmentId = v === "all" ? "" : v;
                const shouldResetAssignee =
                  Boolean(nextDepartmentId) &&
                  Boolean(filters.assignee_id) &&
                  filters.assignee_id !== "unassigned" &&
                  !members.some(
                    (m) =>
                      m.id === filters.assignee_id &&
                      m.department_id === nextDepartmentId
                  );
                const shouldResetAuthor =
                  Boolean(nextDepartmentId) &&
                  Boolean(filters.created_by_id) &&
                  !members.some(
                    (m) =>
                      m.id === filters.created_by_id &&
                      m.department_id === nextDepartmentId
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
          )}

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
                {memberOptions.map((m) => (
                  <SelectItem key={`assignee:${m.id}`} value={`assignee:${m.id}`}>
                    <span className="flex items-center gap-2">
                      <UserAvatar name={m.full_name} avatarUrl={m.avatar_url} size="sm" />
                      <span className="truncate">{m.full_name}</span>
                    </span>
                  </SelectItem>
                ))}
              </SelectGroup>

              <SelectSeparator />

              <SelectGroup>
                <SelectLabel>Автор</SelectLabel>
                {memberOptions.map((m) => (
                  <SelectItem key={`author:${m.id}`} value={`author:${m.id}`}>
                    <span className="flex items-center gap-2">
                      <UserAvatar name={m.full_name} avatarUrl={m.avatar_url} size="sm" />
                      <span className="truncate">{m.full_name}</span>
                    </span>
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>
      </div>

      {activeFilters.length > 0 && (
        <div className="mt-2 flex items-center gap-1.5 flex-wrap border-t border-border/60 pt-2 animate-in fade-in slide-in-from-top-1 duration-200">
          <SlidersHorizontal className="h-3.5 w-3.5 text-muted-foreground" />
          {activeFilters.map((f) => (
            <button
              key={f.key}
              type="button"
              onClick={() => removeFilter(f.key)}
              className="inline-flex max-w-full items-center gap-1.5 rounded-full border border-primary/20 bg-primary/10 text-primary px-2.5 py-1 text-xs font-medium hover:bg-primary/20 group"
            >
              <span className="truncate">{f.label}</span>
              <X className="h-3 w-3 opacity-60 group-hover:opacity-100" />
            </button>
          ))}
          {activeFilters.length > 0 && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => onFiltersChange(EMPTY_FILTERS)}
              className="h-7 rounded-full px-2 text-xs text-muted-foreground hover:text-foreground"
            >
              <X className="h-3.5 w-3.5" />
              Сбросить
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
