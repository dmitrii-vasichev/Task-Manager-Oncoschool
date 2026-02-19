"use client";

import type { ReactNode } from "react";
import {
  CalendarDays,
  Clock3,
  Filter,
  Hand,
  Repeat2,
  Video,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { formatUtcClockForSchedule } from "@/lib/meetingDateTime";
import { getDayLabel } from "@/lib/meetingDayTheme";
import { DAY_OF_WEEK_SHORT, RECURRENCE_LABELS, type MeetingSchedule } from "@/lib/types";
import { cn } from "@/lib/utils";

const WEEK_DAYS = [1, 2, 3, 4, 5, 6, 7] as const;
type WeekDay = (typeof WEEK_DAYS)[number];

const DAY_ACTIVE_CLASSES: Record<WeekDay, string> = {
  1: "bg-blue-500/15 text-blue-700 border-blue-500/30",
  2: "bg-violet-500/15 text-violet-700 border-violet-500/30",
  3: "bg-emerald-500/15 text-emerald-700 border-emerald-500/30",
  4: "bg-amber-500/15 text-amber-700 border-amber-500/30",
  5: "bg-rose-500/15 text-rose-700 border-rose-500/30",
  6: "bg-cyan-500/15 text-cyan-700 border-cyan-500/30",
  7: "bg-orange-500/15 text-orange-700 border-orange-500/30",
};

const DAY_TEXT_CLASSES: Record<WeekDay, string> = {
  1: "text-blue-700",
  2: "text-violet-700",
  3: "text-emerald-700",
  4: "text-amber-700",
  5: "text-rose-700",
  6: "text-cyan-700",
  7: "text-orange-700",
};

function normalizeDay(dayOfWeek: number): WeekDay {
  if (Number.isInteger(dayOfWeek) && dayOfWeek >= 1 && dayOfWeek <= 7) {
    return dayOfWeek as WeekDay;
  }
  return 1;
}

export type ScheduleTemplatesFilter =
  | { type: "all" }
  | { type: "manual_only" }
  | { type: "schedule_id"; scheduleId: string };

export interface ScheduleTemplatesPanelProps {
  schedules: MeetingSchedule[];
  selectedFilter: ScheduleTemplatesFilter;
  onFilterChange: (filter: ScheduleTemplatesFilter) => void;
  totalCount?: number;
  manualCount?: number;
  scheduleCounts?: Record<string, number>;
  className?: string;
}

export function ScheduleTemplatesPanel({
  schedules,
  selectedFilter,
  onFilterChange,
  totalCount,
  manualCount,
  scheduleCounts,
  className,
}: ScheduleTemplatesPanelProps) {
  const sortedSchedules = [...schedules].sort(
    (a, b) =>
      a.day_of_week - b.day_of_week ||
      a.time_utc.localeCompare(b.time_utc) ||
      a.title.localeCompare(b.title, "ru"),
  );

  return (
    <div className={cn("rounded-2xl border border-border/60 bg-card/60", className)}>
      <div className="border-b border-border/50 p-4">
        <div className="flex items-center gap-2 text-2xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">
          <Filter className="h-3.5 w-3.5" />
          Фильтры таймлайна
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <FilterChip
            icon={<CalendarDays className="h-3.5 w-3.5" />}
            label="Все"
            count={totalCount}
            active={selectedFilter.type === "all"}
            onClick={() => onFilterChange({ type: "all" })}
          />
          <FilterChip
            icon={<Hand className="h-3.5 w-3.5" />}
            label="Ручные"
            count={manualCount}
            active={selectedFilter.type === "manual_only"}
            onClick={() => onFilterChange({ type: "manual_only" })}
          />
        </div>
      </div>

      <div className="space-y-3 p-4">
        {sortedSchedules.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border/60 bg-muted/20 p-4 text-xs text-muted-foreground">
            Нет шаблонов расписания
          </div>
        ) : (
          sortedSchedules.map((schedule) => {
            const normalizedDay = normalizeDay(schedule.day_of_week);
            const isSelected =
              selectedFilter.type === "schedule_id" &&
              selectedFilter.scheduleId === schedule.id;
            const scheduleCount = scheduleCounts?.[schedule.id];
            const displayTime = formatUtcClockForSchedule(schedule.time_utc);

            return (
              <button
                key={schedule.id}
                type="button"
                onClick={() =>
                  onFilterChange({ type: "schedule_id", scheduleId: schedule.id })
                }
                className={cn(
                  "w-full rounded-xl border p-3 text-left transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30 focus-visible:ring-offset-1",
                  isSelected
                    ? "border-primary/40 bg-primary/5 shadow-sm"
                    : "border-border/60 bg-card hover:border-border hover:bg-muted/20 hover:shadow-sm",
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-heading font-semibold text-foreground">
                      {schedule.title}
                    </p>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-2xs text-muted-foreground">
                      <span className="inline-flex items-center gap-1">
                        <Clock3 className="h-3 w-3" />
                        {displayTime.moscow}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <Repeat2 className="h-3 w-3" />
                        {RECURRENCE_LABELS[schedule.recurrence]}
                      </span>
                    </div>
                    <p className="mt-1 text-2xs text-muted-foreground/80">
                      {displayTime.local}
                    </p>
                  </div>

                  <div className="flex flex-col items-end gap-1">
                    {!schedule.is_active && (
                      <Badge
                        variant="outline"
                        className="rounded-md border-border/60 text-2xs text-muted-foreground"
                      >
                        Неактивно
                      </Badge>
                    )}
                    {typeof scheduleCount === "number" && (
                      <Badge variant="secondary" className="rounded-md text-2xs">
                        {scheduleCount}
                      </Badge>
                    )}
                  </div>
                </div>

                <div className="mt-3 grid grid-cols-7 gap-1">
                  {WEEK_DAYS.map((day) => (
                    <div
                      key={day}
                      className={cn(
                        "flex h-7 items-center justify-center rounded-md border text-2xs font-semibold",
                        day === normalizedDay
                          ? DAY_ACTIVE_CLASSES[day]
                          : "border-border/40 bg-muted/40 text-muted-foreground/55",
                      )}
                    >
                      {DAY_OF_WEEK_SHORT[day]}
                    </div>
                  ))}
                </div>

                <p className="mt-2 text-2xs font-medium text-muted-foreground">
                  Активный день:{" "}
                  <span className={cn("font-semibold", DAY_TEXT_CLASSES[normalizedDay])}>
                    {getDayLabel(normalizedDay)}
                  </span>
                </p>

                <div className="mt-2 flex items-center gap-1.5 text-2xs">
                  <Video
                    className={cn(
                      "h-3 w-3",
                      schedule.zoom_enabled ? "text-blue-600" : "text-muted-foreground/50",
                    )}
                  />
                  <span className="text-muted-foreground">
                    {schedule.zoom_enabled ? "Zoom включен" : "Без Zoom"}
                  </span>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}

function FilterChip({
  icon,
  label,
  count,
  active,
  onClick,
}: {
  icon: ReactNode;
  label: string;
  count?: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex w-full items-center justify-between gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30 focus-visible:ring-offset-1 sm:w-auto",
        active
          ? "border-primary/40 bg-primary/10 text-primary"
          : "border-border/60 bg-card text-muted-foreground hover:text-foreground hover:border-border",
      )}
    >
      {icon}
      {label}
      {typeof count === "number" && (
        <span
          className={cn(
            "rounded-md px-1.5 py-0.5 text-2xs font-semibold leading-none",
            active ? "bg-primary/15 text-primary" : "bg-muted text-muted-foreground",
          )}
        >
          {count}
        </span>
      )}
    </button>
  );
}
