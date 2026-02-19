"use client";

import { useState } from "react";
import {
  CalendarDays,
  Clock3,
  ExternalLink,
  Loader2,
  Trash2,
  Video,
  VideoOff,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { PROJECT_TIMEZONE, PROJECT_TIMEZONE_LABEL } from "@/lib/meetingDateTime";
import type {
  TimelineMeetingItem,
  TimelineMeetingSource,
} from "@/lib/meetingsTimeline";
import { MEETING_STATUS_LABELS, type MeetingStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const STATUS_STYLES: Record<MeetingStatus, string> = {
  scheduled: "bg-blue-500/10 text-blue-600 border-blue-500/20",
  in_progress: "bg-amber-500/10 text-amber-600 border-amber-500/20",
  completed: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  cancelled: "bg-muted text-muted-foreground border-border/40",
};

const SOURCE_STYLES: Record<TimelineMeetingSource, string> = {
  schedule: "bg-primary/10 text-primary border-primary/20",
  manual: "bg-slate-500/10 text-slate-600 border-slate-500/20",
  schedule_missing: "bg-rose-500/10 text-rose-600 border-rose-500/20",
};

const DATE_FORMATTER = new Intl.DateTimeFormat("ru-RU", {
  timeZone: PROJECT_TIMEZONE,
  day: "2-digit",
  month: "long",
  year: "numeric",
});

export interface TimelineMeetingCardProps {
  item: TimelineMeetingItem;
  onOpen?: (item: TimelineMeetingItem) => void;
  isModerator?: boolean;
  onDeleteMeeting?: (item: TimelineMeetingItem) => Promise<void>;
  className?: string;
}

export function TimelineMeetingCard({
  item,
  onOpen,
  isModerator = false,
  onDeleteMeeting,
  className,
}: TimelineMeetingCardProps) {
  const effectiveStatus = item.meeting.effective_status || item.meeting.status;
  const sourceLabel = getSourceLabel(item.source);
  const sourceDetails = getSourceDetails(item);
  const zoomStatus = getZoomStatus(item);
  const title = item.meeting.title || item.schedule?.title || "Встреча без названия";
  const canDelete = isModerator && Boolean(onDeleteMeeting);
  const [deleting, setDeleting] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const isInteractive = Boolean(onOpen);

  return (
    <>
      <article
        className={cn(
          "rounded-xl border border-border/60 bg-card p-3 transition-colors",
          isInteractive &&
            "cursor-pointer hover:border-border hover:bg-muted/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30 focus-visible:ring-offset-1",
          className,
        )}
        role={isInteractive ? "button" : undefined}
        tabIndex={isInteractive ? 0 : undefined}
        aria-label={isInteractive ? `Открыть встречу «${title}»` : undefined}
        onClick={isInteractive ? () => onOpen?.(item) : undefined}
        onKeyDown={
          isInteractive
            ? (event) => {
                if (event.target !== event.currentTarget) {
                  return;
                }
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onOpen?.(item);
                }
              }
            : undefined
        }
      >
        <div className="flex flex-wrap items-start justify-between gap-2">
          <Badge
            variant="outline"
            className={cn(
              "rounded-lg border px-2 py-0.5 text-2xs font-medium",
              SOURCE_STYLES[item.source],
            )}
          >
            {sourceLabel}
          </Badge>
          <Badge
            variant="outline"
            className={cn(
              "rounded-lg border px-2 py-0.5 text-2xs font-medium",
              STATUS_STYLES[effectiveStatus],
            )}
          >
            {MEETING_STATUS_LABELS[effectiveStatus]}
          </Badge>
        </div>

        <h4 className="mt-2 text-sm font-heading font-semibold text-foreground line-clamp-2">
          {title}
        </h4>
        <p className="mt-1 text-2xs text-muted-foreground">{sourceDetails}</p>

        <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <CalendarDays className="h-3.5 w-3.5" />
            {DATE_FORMATTER.format(item.meetingAt)}
          </span>
          <span className="inline-flex items-center gap-1">
            <Clock3 className="h-3.5 w-3.5" />
            {item.meetingTimeLabel} {PROJECT_TIMEZONE_LABEL}
          </span>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-border/40 pt-3">
          <div className="inline-flex items-center gap-1.5 text-2xs text-muted-foreground">
            {item.meeting.zoom_join_url ? (
              <Video className="h-3.5 w-3.5 text-blue-600" />
            ) : (
              <VideoOff className="h-3.5 w-3.5 text-muted-foreground/60" />
            )}
            <span>{zoomStatus}</span>
          </div>

          <div className="ml-auto flex items-center gap-1.5">
            {item.meeting.zoom_join_url && (
              <Button
                asChild
                variant="outline"
                size="sm"
                className="h-7 rounded-lg px-2 text-2xs"
              >
                <a
                  href={item.meeting.zoom_join_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(event) => event.stopPropagation()}
                >
                  Войти
                  <ExternalLink className="h-3 w-3 ml-1" />
                </a>
              </Button>
            )}
            {canDelete && (
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-7 w-7 rounded-lg text-muted-foreground hover:text-destructive"
                onClick={(event) => {
                  event.stopPropagation();
                  setShowDeleteDialog(true);
                }}
                disabled={deleting}
                title="Удалить встречу"
              >
                {deleting ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Trash2 className="h-3.5 w-3.5" />
                )}
              </Button>
            )}
          </div>
        </div>
      </article>

      {showDeleteDialog && onDeleteMeeting && (
        <Dialog open onOpenChange={(open) => !open && setShowDeleteDialog(false)}>
          <DialogContent className="sm:max-w-sm">
            <DialogHeader>
              <DialogTitle className="font-heading">Удалить встречу</DialogTitle>
              <DialogDescription className="text-sm text-muted-foreground pt-1">
                {item.meeting.zoom_meeting_id
                  ? <>Встреча <span className="font-medium text-foreground">&laquo;{title}&raquo;</span> и связанная Zoom-конференция будут удалены безвозвратно.</>
                  : <>Встреча <span className="font-medium text-foreground">&laquo;{title}&raquo;</span> будет удалена безвозвратно.</>
                }
              </DialogDescription>
            </DialogHeader>
            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="outline"
                className="rounded-xl"
                onClick={() => setShowDeleteDialog(false)}
                disabled={deleting}
              >
                Отмена
              </Button>
              <Button
                variant="destructive"
                className="rounded-xl"
                disabled={deleting}
                onClick={async () => {
                  setDeleting(true);
                  try {
                    await onDeleteMeeting(item);
                  } finally {
                    setDeleting(false);
                    setShowDeleteDialog(false);
                  }
                }}
              >
                {deleting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Удаление...
                  </>
                ) : (
                  <>
                    <Trash2 className="mr-2 h-4 w-4" />
                    Удалить
                  </>
                )}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </>
  );
}

function getSourceLabel(source: TimelineMeetingSource): string {
  if (source === "schedule") return "Из расписания";
  if (source === "manual") return "Ручная";
  return "Шаблон удалён";
}

function getSourceDetails(item: TimelineMeetingItem): string {
  if (item.source === "manual") {
    return "Создана вручную";
  }

  if (item.source === "schedule_missing") {
    return "Оригинальный шаблон расписания удалён";
  }

  return item.schedule?.title
    ? `Шаблон: ${item.schedule.title}`
    : "Шаблон расписания";
}

function getZoomStatus(item: TimelineMeetingItem): string {
  if (item.meeting.zoom_join_url) {
    return "Zoom готов";
  }

  if (item.meeting.zoom_meeting_id) {
    return "Zoom запланирован";
  }

  return "Без Zoom";
}
