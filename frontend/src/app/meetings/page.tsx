"use client";

import { useState, useMemo, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Calendar, CalendarPlus, Loader2, Plus, Video } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { useMeetingSchedules } from "@/hooks/useMeetingSchedules";
import { useMeetings } from "@/hooks/useMeetings";
import { useTeam } from "@/hooks/useTeam";
import { useDepartments } from "@/hooks/useDepartments";
import { PermissionService } from "@/lib/permissions";
import { api } from "@/lib/api";
import { useToast } from "@/components/shared/Toast";
import { DatePicker } from "@/components/shared/DatePicker";
import { TimePicker } from "@/components/shared/TimePicker";
import { EmptyState } from "@/components/shared/EmptyState";
import { ScheduleCard } from "@/components/meetings/ScheduleCard";
import { ScheduleForm } from "@/components/meetings/ScheduleForm";
import {
  ScheduleTemplatesPanel,
  type ScheduleTemplatesFilter,
} from "@/components/meetings/ScheduleTemplatesPanel";
import { TimelineDaySection } from "@/components/meetings/TimelineDaySection";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import type {
  MeetingSchedule,
  MeetingScheduleCreateRequest,
  TelegramNotificationTarget,
} from "@/lib/types";
import {
  buildMeetingsTimeline,
  type TimelineDayGroup,
  type TimelineMeetingItem,
} from "@/lib/meetingsTimeline";
import {
  PROJECT_TIMEZONE_LABEL,
  zonedDateTimeToUtcIso,
} from "@/lib/meetingDateTime";

export default function MeetingsPage() {
  const router = useRouter();
  const { user } = useCurrentUser();
  const isModerator = user ? PermissionService.isModerator(user) : false;

  const {
    schedules,
    loading: schedulesLoading,
    refetch: refetchSchedules,
  } = useMeetingSchedules();
  const {
    meetings: upcomingMeetings,
    loading: upcomingLoading,
    refetch: refetchUpcoming,
  } = useMeetings({ upcoming: true });
  const {
    meetings: pastMeetings,
    loading: pastLoading,
    refetch: refetchPast,
  } = useMeetings({ past: true });
  const { members } = useTeam();
  const { departments } = useDepartments();

  const [timelineFilter, setTimelineFilter] =
    useState<ScheduleTemplatesFilter>({ type: "all" });

  // Telegram targets (for schedule form)
  const [telegramTargets, setTelegramTargets] = useState<TelegramNotificationTarget[]>([]);
  useEffect(() => {
    if (isModerator) {
      api.getTelegramTargets().then(setTelegramTargets).catch(() => {});
    }
  }, [isModerator]);

  // Schedule form state
  const [editSchedule, setEditSchedule] = useState<MeetingSchedule | null>(null);
  const [showScheduleForm, setShowScheduleForm] = useState(false);

  // Create meeting dialog
  const [showCreateMeeting, setShowCreateMeeting] = useState(false);

  // Delete confirmation
  const [deleteTarget, setDeleteTarget] = useState<MeetingSchedule | null>(null);

  const { toastSuccess, toastError } = useToast();

  const sortedSchedules = useMemo(
    () =>
      [...schedules].sort(
        (a, b) =>
          a.day_of_week - b.day_of_week ||
          a.time_utc.localeCompare(b.time_utc) ||
          a.title.localeCompare(b.title, "ru"),
      ),
    [schedules],
  );

  const timelineDays = useMemo(
    () => buildMeetingsTimeline({ upcomingMeetings, pastMeetings, schedules }),
    [upcomingMeetings, pastMeetings, schedules],
  );

  const timelineCounts = useMemo(() => {
    const bySchedule: Record<string, number> = {};
    let total = 0;
    let manual = 0;

    for (const day of timelineDays) {
      for (const item of day.items) {
        total += 1;
        if (item.source === "manual") {
          manual += 1;
        }
        if (item.scheduleId) {
          bySchedule[item.scheduleId] = (bySchedule[item.scheduleId] ?? 0) + 1;
        }
      }
    }

    return {
      total,
      manual,
      bySchedule,
    };
  }, [timelineDays]);

  const filteredTimelineDays = useMemo(
    () => filterTimelineDays(timelineDays, timelineFilter),
    [timelineDays, timelineFilter],
  );

  const selectedSchedule = useMemo(() => {
    if (timelineFilter.type !== "schedule_id") {
      return null;
    }

    return (
      sortedSchedules.find((schedule) => schedule.id === timelineFilter.scheduleId) ?? null
    );
  }, [timelineFilter, sortedSchedules]);

  const filteredCount = useMemo(
    () => filteredTimelineDays.reduce((total, day) => total + day.items.length, 0),
    [filteredTimelineDays],
  );

  useEffect(() => {
    if (timelineFilter.type !== "schedule_id") {
      return;
    }

    const exists = sortedSchedules.some(
      (schedule) => schedule.id === timelineFilter.scheduleId,
    );

    if (!exists) {
      setTimelineFilter({ type: "all" });
    }
  }, [timelineFilter, sortedSchedules]);

  // Handlers
  const handleCreateSchedule = useCallback(
    async (data: MeetingScheduleCreateRequest) => {
      await api.createMeetingSchedule(data);
      toastSuccess("Расписание создано");
      refetchSchedules();
      refetchUpcoming();
    },
    [refetchSchedules, refetchUpcoming, toastSuccess],
  );

  const handleUpdateSchedule = useCallback(
    async (data: MeetingScheduleCreateRequest) => {
      if (!editSchedule) {
        return;
      }
      await api.updateMeetingSchedule(editSchedule.id, data);
      toastSuccess("Расписание обновлено");
      refetchSchedules();
      refetchUpcoming();
    },
    [editSchedule, refetchSchedules, refetchUpcoming, toastSuccess],
  );

  const handleDeleteSchedule = useCallback(
    async (schedule: MeetingSchedule) => {
      try {
        await api.deleteMeetingSchedule(schedule.id);
        toastSuccess("Расписание удалено");
        refetchSchedules();
      } catch (e) {
        toastError(e instanceof Error ? e.message : "Ошибка удаления");
      } finally {
        setDeleteTarget(null);
      }
    },
    [refetchSchedules, toastSuccess, toastError],
  );

  const handleDeleteMeeting = useCallback(
    async (meeting: { id: string }) => {
      try {
        await api.deleteMeeting(meeting.id);
        toastSuccess("Встреча удалена");
        refetchUpcoming();
        refetchPast();
      } catch (e) {
        toastError(e instanceof Error ? e.message : "Ошибка удаления");
      }
    },
    [refetchUpcoming, refetchPast, toastSuccess, toastError],
  );

  const handleDeleteTimelineMeeting = useCallback(
    async (item: TimelineMeetingItem) => {
      await handleDeleteMeeting(item.meeting);
    },
    [handleDeleteMeeting],
  );

  const loading = schedulesLoading || upcomingLoading || pastLoading;

  if (loading) {
    return (
      <div className="grid animate-in gap-6 fade-in duration-300 lg:grid-cols-[minmax(280px,320px)_minmax(0,1fr)] xl:grid-cols-[minmax(320px,360px)_minmax(0,1fr)]">
        <div className="space-y-4">
          <Skeleton className="h-64 rounded-2xl" />
          <Skeleton className="h-80 rounded-2xl" />
        </div>
        <div className="space-y-4">
          <Skeleton className="h-10 w-64 rounded-xl" />
          {[...Array(3)].map((_, index) => (
            <Skeleton key={index} className="h-56 rounded-2xl" />
          ))}
        </div>
      </div>
    );
  }

  const emptyState = getTimelineEmptyState(timelineFilter, selectedSchedule?.title);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="grid gap-6 lg:grid-cols-[minmax(280px,320px)_minmax(0,1fr)] xl:grid-cols-[minmax(320px,360px)_minmax(0,1fr)]">
        <aside className="self-start space-y-4 lg:sticky lg:top-6">
          <ScheduleTemplatesPanel
            schedules={sortedSchedules}
            selectedFilter={timelineFilter}
            onFilterChange={setTimelineFilter}
            totalCount={timelineCounts.total}
            manualCount={timelineCounts.manual}
            scheduleCounts={timelineCounts.bySchedule}
          />

          <section className="overflow-hidden rounded-2xl border border-border/60 bg-card/60">
            <header className="flex items-center justify-between border-b border-border/50 p-4">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/10">
                  <Calendar className="h-4.5 w-4.5 text-primary" />
                </div>
                <h2 className="text-sm font-heading font-semibold">Управление расписаниями</h2>
              </div>

              {isModerator && (
                <Button
                  size="sm"
                  className="gap-1.5 rounded-xl"
                  onClick={() => {
                    setEditSchedule(null);
                    setShowScheduleForm(true);
                  }}
                >
                  <Plus className="h-4 w-4" />
                  Новое
                </Button>
              )}
            </header>

            <div className="space-y-3 p-4">
              {sortedSchedules.length === 0 ? (
                <div className="rounded-xl border border-dashed border-border/60 bg-muted/20 p-5 text-center">
                  <Calendar className="mx-auto mb-2 h-7 w-7 text-muted-foreground/40" />
                  <p className="text-xs text-muted-foreground">Нет активных расписаний</p>
                </div>
              ) : (
                sortedSchedules.map((schedule, index) => (
                  <div
                    key={schedule.id}
                    className={`animate-fade-in-up stagger-${Math.min(index + 1, 6)}`}
                  >
                    <ScheduleCard
                      schedule={schedule}
                      members={members}
                      isModerator={isModerator}
                      onEdit={(target) => {
                        setEditSchedule(target);
                        setShowScheduleForm(true);
                      }}
                      onDelete={setDeleteTarget}
                    />
                  </div>
                ))
              )}
            </div>
          </section>
        </aside>

        <section className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-heading font-semibold">Единый таймлайн встреч</h2>
              <p className="text-xs text-muted-foreground">Показано {filteredCount} встреч</p>
            </div>

            {isModerator && (
              <Button
                size="sm"
                variant="outline"
                className="w-full gap-1.5 rounded-xl sm:w-auto"
                onClick={() => setShowCreateMeeting(true)}
              >
                <CalendarPlus className="h-4 w-4" />
                Создать встречу
              </Button>
            )}
          </div>

          {filteredTimelineDays.length === 0 ? (
            <EmptyState
              variant="meetings"
              title={emptyState.title}
              description={emptyState.description}
              actionLabel={
                isModerator && emptyState.allowCreateMeeting ? "Создать встречу" : undefined
              }
              onAction={
                isModerator && emptyState.allowCreateMeeting
                  ? () => setShowCreateMeeting(true)
                  : undefined
              }
            />
          ) : (
            <div className="space-y-4">
              {filteredTimelineDays.map((day, index) => (
                <div
                  key={day.dayKey}
                  className={`animate-fade-in-up stagger-${Math.min(index + 1, 6)}`}
                >
                  <TimelineDaySection
                    day={day}
                    onMeetingOpen={(item) => router.push(`/meetings/${item.id}`)}
                    isModerator={isModerator}
                    onDeleteMeeting={
                      isModerator ? handleDeleteTimelineMeeting : undefined
                    }
                  />
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      {showScheduleForm && (
        <ScheduleForm
          schedule={editSchedule}
          members={members}
          departments={departments}
          telegramTargets={telegramTargets}
          onSave={editSchedule ? handleUpdateSchedule : handleCreateSchedule}
          onClose={() => {
            setShowScheduleForm(false);
            setEditSchedule(null);
          }}
        />
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title={`Удалить расписание «${deleteTarget?.title}»?`}
        description="Расписание будет удалено. Уже созданные встречи останутся."
        onConfirm={() => deleteTarget && handleDeleteSchedule(deleteTarget)}
      />

      {showCreateMeeting && (
        <CreateMeetingDialog
          onClose={() => setShowCreateMeeting(false)}
          onCreated={() => {
            refetchUpcoming();
            refetchPast();
            setShowCreateMeeting(false);
          }}
        />
      )}
    </div>
  );
}

type TimelineEmptyState = {
  title: string;
  description: string;
  allowCreateMeeting: boolean;
};

function filterTimelineDays(
  days: TimelineDayGroup[],
  filter: ScheduleTemplatesFilter,
): TimelineDayGroup[] {
  return days
    .map((day) => {
      const items = day.items.filter((item) => matchesTimelineFilter(item, filter));
      return {
        ...day,
        items,
      };
    })
    .filter((day) => day.items.length > 0);
}

function matchesTimelineFilter(
  item: TimelineMeetingItem,
  filter: ScheduleTemplatesFilter,
): boolean {
  if (filter.type === "all") {
    return true;
  }

  if (filter.type === "manual_only") {
    return item.source === "manual";
  }

  return item.scheduleId === filter.scheduleId;
}

function getTimelineEmptyState(
  filter: ScheduleTemplatesFilter,
  scheduleTitle?: string,
): TimelineEmptyState {
  if (filter.type === "manual_only") {
    return {
      title: "Нет встреч, созданных вручную",
      description:
        "Создайте ручную встречу, чтобы она появилась в единой ленте рядом со встречами из расписания.",
      allowCreateMeeting: true,
    };
  }

  if (filter.type === "schedule_id") {
    const title = scheduleTitle
      ? `По шаблону «${scheduleTitle}» пока нет встреч`
      : "По выбранному шаблону пока нет встреч";

    return {
      title,
      description:
        "Встречи появятся после следующего запуска расписания или после ручного создания связанной встречи.",
      allowCreateMeeting: false,
    };
  }

  return {
    title: "Лента встреч пока пуста",
    description:
      "Создайте встречу вручную или добавьте расписание, чтобы заполнить единый таймлайн.",
    allowCreateMeeting: true,
  };
}

// ============================================
// Create Meeting Dialog (manual, no schedule)
// ============================================

function CreateMeetingDialog({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const { toastSuccess, toastError } = useToast();
  const [title, setTitle] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("15:00");
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [zoomEnabled, setZoomEnabled] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!title.trim()) {
      setError("Введите название");
      return;
    }
    if (!date) {
      setError("Выберите дату");
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const meetingDate = zonedDateTimeToUtcIso(date, time);
      await api.createMeetingManual({
        title: title.trim(),
        meeting_date: meetingDate,
        zoom_enabled: zoomEnabled,
        duration_minutes: durationMinutes,
      });
      toastSuccess("Встреча создана");
      onCreated();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Ошибка создания";
      setError(msg);
      toastError(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="font-heading">Создать встречу</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 pt-2">
          <div>
            <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Название
            </Label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Название встречи"
              className="mt-1.5 rounded-xl"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Дата
              </Label>
              <DatePicker
                value={date}
                onChange={setDate}
                placeholder="Выбрать"
                className="w-full mt-1.5 rounded-xl"
              />
            </div>
            <div>
              <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Время ({PROJECT_TIMEZONE_LABEL})
              </Label>
              <TimePicker
                value={time}
                onChange={setTime}
                className="mt-1.5 rounded-xl"
              />
            </div>
          </div>

          <div>
            <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Длительность
            </Label>
            <select
              value={durationMinutes}
              onChange={(e) => setDurationMinutes(Number(e.target.value))}
              className="mt-1.5 w-full h-10 rounded-xl border border-input bg-background px-3 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            >
              <option value={30}>30 минут</option>
              <option value={45}>45 минут</option>
              <option value={60}>1 час</option>
              <option value={90}>1.5 часа</option>
              <option value={120}>2 часа</option>
            </select>
          </div>

          <div className="flex items-center justify-between p-3 rounded-xl bg-muted/40 border border-border/40">
            <div className="flex items-center gap-2">
              <Video className="h-4 w-4 text-blue-500" />
              <span className="text-sm font-medium">Создать Zoom-конференцию</span>
            </div>
            <Switch checked={zoomEnabled} onCheckedChange={setZoomEnabled} />
          </div>

          {error && (
            <div className="rounded-xl bg-destructive/10 border border-destructive/20 p-3">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}

          <div className="flex gap-2 justify-end pt-2">
            <Button
              variant="outline"
              className="rounded-xl"
              onClick={onClose}
              disabled={saving}
            >
              Отмена
            </Button>
            <Button className="rounded-xl" onClick={handleCreate} disabled={saving}>
              {saving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Создание...
                </>
              ) : (
                "Создать"
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
