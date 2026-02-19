"use client";

import {
  Bell,
  Video,
  Settings,
  Trash2,
  Clock,
  Repeat,
  Users,
  SkipForward,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { UserAvatar } from "@/components/shared/UserAvatar";
import type { MeetingSchedule, TeamMember } from "@/lib/types";
import { RECURRENCE_LABELS } from "@/lib/types";
import { formatUtcClockAsMoscowWithLocal, formatUtcClockForSchedule } from "@/lib/meetingDateTime";
import { getDayShort, getDayTheme } from "@/lib/meetingDayTheme";

interface ScheduleCardProps {
  schedule: MeetingSchedule;
  members: TeamMember[];
  isModerator: boolean;
  onEdit: (schedule: MeetingSchedule) => void;
  onDelete: (schedule: MeetingSchedule) => void;
}

export function ScheduleCard({
  schedule,
  members,
  isModerator,
  onEdit,
  onDelete,
}: ScheduleCardProps) {
  const displayTime = formatUtcClockForSchedule(schedule.time_utc);
  const dayTheme = getDayTheme(schedule.day_of_week);

  // Resolve participant names from IDs
  const participants = schedule.participant_ids
    .map((pid) => members.find((m) => m.id === pid))
    .filter(Boolean) as TeamMember[];

  return (
    <div className="group relative overflow-hidden rounded-2xl border border-border/60 bg-card transition-all duration-200 hover:border-border/80 hover:shadow-md">
      {/* Subtle decorative accent */}
      <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-primary/3 to-transparent rounded-bl-3xl pointer-events-none" />

      <div className="p-3 sm:p-5">
        {/* Top row: day badge + title + actions */}
        <div className="flex items-start gap-2.5 sm:gap-3">
          {/* Day badge */}
          <div
            className={`shrink-0 flex items-center justify-center h-10 w-10 sm:h-11 sm:w-11 rounded-xl border font-heading font-bold text-sm ${dayTheme.badgeClassName}`}
          >
            {getDayShort(schedule.day_of_week)}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <h3 className="font-heading font-semibold text-sm text-foreground truncate">
              {schedule.title}
            </h3>

            {/* Time and recurrence block */}
            <div className="mt-1 space-y-1">
              <div className="flex flex-wrap items-center gap-x-1.5 gap-y-1 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                <span>{displayTime.moscow}</span>
                <span className="text-border mx-0.5">·</span>
                <span>{schedule.duration_minutes} мин</span>
              </div>
              <div className="text-2xs text-muted-foreground pl-4">
                {displayTime.local}
              </div>
              <Badge
                variant="secondary"
                className="rounded-md text-2xs font-medium px-1.5 py-0 h-5"
              >
                <Repeat className="h-2.5 w-2.5 mr-0.5" />
                {RECURRENCE_LABELS[schedule.recurrence]}
              </Badge>
            </div>
          </div>

          {/* Actions (moderator only, visible on hover) */}
          {isModerator && (
            <div className="flex shrink-0 items-center gap-1 opacity-100 transition-opacity sm:opacity-0 sm:group-hover:opacity-100 sm:group-focus-within:opacity-100">
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 sm:h-8 sm:w-8 rounded-lg text-muted-foreground hover:text-foreground"
                onClick={() => onEdit(schedule)}
              >
                <Settings className="h-3.5 w-3.5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 sm:h-8 sm:w-8 rounded-lg text-muted-foreground hover:text-destructive"
                onClick={() => onDelete(schedule)}
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </div>
          )}
        </div>

        {/* Bottom row: indicators + participants */}
        <div className="mt-2.5 flex flex-wrap items-center gap-2.5 border-t border-border/40 pt-2.5 sm:mt-3 sm:gap-3 sm:pt-3">
          {/* Indicators */}
          <div className="flex flex-wrap items-center gap-2">
            {schedule.zoom_enabled && (
              <div className="flex items-center gap-1 text-2xs text-muted-foreground">
                <Video className="h-3 w-3 text-blue-500" />
                <span>Zoom</span>
              </div>
            )}
            {schedule.reminder_enabled && (
              <div className="flex items-center gap-1 text-2xs text-muted-foreground">
                <Bell className="h-3 w-3 text-amber-500" />
                <span>за {schedule.reminder_minutes_before} мин</span>
              </div>
            )}
            {schedule.next_occurrence_skip && (
              <div className="flex items-center gap-1 text-2xs text-amber-600 font-medium">
                <SkipForward className="h-3 w-3" />
                <span>Следующая отменена</span>
              </div>
            )}
            {!schedule.next_occurrence_skip && schedule.next_occurrence_time_override && (
              <div className="flex items-center gap-1 text-2xs text-blue-600 font-medium">
                <Clock className="h-3 w-3" />
                <span>
                  Перенос на {formatUtcClockAsMoscowWithLocal(schedule.next_occurrence_time_override)}
                </span>
              </div>
            )}
          </div>

          <div className="hidden flex-1 sm:block" />

          {/* Participants */}
          {participants.length > 0 ? (
            <div className="ml-auto flex items-center gap-1">
              <div className="flex -space-x-1.5">
                {participants.slice(0, 4).map((p) => (
                  <UserAvatar key={p.id} name={p.full_name} avatarUrl={p.avatar_url} size="sm" />
                ))}
              </div>
              {participants.length > 4 && (
                <span className="text-2xs text-muted-foreground ml-1">
                  +{participants.length - 4}
                </span>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-1 text-2xs text-muted-foreground/50">
              <Users className="h-3 w-3" />
              <span>Нет участников</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
