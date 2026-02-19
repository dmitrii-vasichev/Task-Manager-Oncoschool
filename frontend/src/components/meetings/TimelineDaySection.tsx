"use client";

import { CalendarDays } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { PROJECT_TIMEZONE } from "@/lib/meetingDateTime";
import { getDayTheme } from "@/lib/meetingDayTheme";
import type { TimelineDayGroup, TimelineMeetingItem } from "@/lib/meetingsTimeline";
import { cn } from "@/lib/utils";
import { TimelineMeetingCard } from "./TimelineMeetingCard";

const DAY_DATE_FORMATTER = new Intl.DateTimeFormat("ru-RU", {
  timeZone: PROJECT_TIMEZONE,
  day: "numeric",
  month: "long",
  year: "numeric",
});

export interface TimelineDaySectionProps {
  day: TimelineDayGroup;
  onMeetingOpen?: (item: TimelineMeetingItem) => void;
  isModerator?: boolean;
  onDeleteMeeting?: (item: TimelineMeetingItem) => Promise<void>;
  className?: string;
}

export function TimelineDaySection({
  day,
  onMeetingOpen,
  isModerator = false,
  onDeleteMeeting,
  className,
}: TimelineDaySectionProps) {
  const dayTheme = getDayTheme(day.dayOfWeek);

  return (
    <section
      className={cn(
        "overflow-hidden rounded-2xl border border-border/60 bg-card/60",
        className,
      )}
    >
      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-border/50 p-4 sm:flex-nowrap sm:items-center">
        <div className="flex min-w-0 items-center gap-3">
          <div
            className={cn(
              "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border text-xs font-semibold",
              dayTheme.badgeClassName,
            )}
          >
            {day.dayShort}
          </div>
          <div className="min-w-0">
            <h3 className="truncate text-sm font-heading font-semibold text-foreground">
              {day.dayLabel}
            </h3>
            <p className="text-xs text-muted-foreground">{formatDayDate(day.dayKey)}</p>
          </div>
        </div>

        <div className="flex w-full flex-wrap items-center justify-end gap-2 sm:w-auto sm:justify-start">
          {day.isToday && (
            <Badge
              variant="outline"
              className="rounded-lg border-primary/25 bg-primary/10 px-2 py-0.5 text-2xs font-medium text-primary"
            >
              Сегодня
            </Badge>
          )}
          <div className="inline-flex items-center gap-1 rounded-lg bg-muted/60 px-2 py-1 text-2xs text-muted-foreground">
            <CalendarDays className="h-3 w-3" />
            {day.items.length}
          </div>
        </div>
      </header>

      <div className="space-y-3 p-4">
        {day.items.map((item) => (
          <TimelineMeetingCard
            key={item.id}
            item={item}
            onOpen={onMeetingOpen}
            isModerator={isModerator}
            onDeleteMeeting={onDeleteMeeting}
          />
        ))}
      </div>
    </section>
  );
}

function formatDayDate(dayKey: string): string {
  const [year, month, day] = dayKey.split("-").map(Number);
  const utcDate = new Date(Date.UTC(year, month - 1, day, 12, 0, 0));
  return DAY_DATE_FORMATTER.format(utcDate);
}
