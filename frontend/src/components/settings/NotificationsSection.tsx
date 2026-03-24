"use client";

import { useState, useEffect } from "react";
import {
  Bell,
  Loader2,
  Save,
  CalendarPlus,
  MessageSquarePlus,
  ClipboardCheck,
  CheckCircle2,
  AlertTriangle,
  ListChecks,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TimePicker } from "@/components/shared/TimePicker";
import { useToast } from "@/components/shared/Toast";
import { api } from "@/lib/api";

interface EventConfig {
  label: string;
  description: string;
  icon: typeof Bell;
  group: "tasks" | "meetings";
}

const EVENT_TYPES: Record<string, EventConfig> = {
  task_created: {
    label: "Создание задачи",
    description: "Когда создаётся новая задача",
    icon: CalendarPlus,
    group: "tasks",
  },
  task_status_changed: {
    label: "Изменение статуса",
    description: "Когда задача меняет статус",
    icon: ClipboardCheck,
    group: "tasks",
  },
  task_completed: {
    label: "Завершение задачи",
    description: "Когда задача отмечена как выполненная",
    icon: CheckCircle2,
    group: "tasks",
  },
  task_overdue: {
    label: "Просроченная задача",
    description: "Когда задача выходит за дедлайн",
    icon: AlertTriangle,
    group: "tasks",
  },
  task_update_added: {
    label: "Новое обновление",
    description: "Когда участник добавляет апдейт к задаче",
    icon: MessageSquarePlus,
    group: "tasks",
  },
  meeting_created: {
    label: "Создание встречи",
    description: "Когда создаётся встреча из summary",
    icon: ListChecks,
    group: "meetings",
  },
};

const TASK_OVERDUE_INTERVAL_OPTIONS = [
  { value: "1", label: "Каждый час" },
  { value: "24", label: "Каждые 24 часа" },
] as const;

export function NotificationsSection() {
  const { toastSuccess, toastError } = useToast();
  const [subscriptions, setSubscriptions] = useState<Record<string, boolean>>(
    {}
  );
  const [taskOverdueIntervalHours, setTaskOverdueIntervalHours] = useState("1");
  const [taskOverdueDailyTimeMsk, setTaskOverdueDailyTimeMsk] = useState("09:00");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getNotificationSubscriptions()
      .then((data) => {
        setSubscriptions(data.subscriptions);
        setTaskOverdueIntervalHours(
          String(data.task_overdue_interval_hours ?? 1)
        );
        setTaskOverdueDailyTimeMsk(data.task_overdue_daily_time_msk ?? "09:00");
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleToggle = (eventType: string) => {
    setSubscriptions((prev) => ({
      ...prev,
      [eventType]: !prev[eventType],
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const intervalHours = Number(taskOverdueIntervalHours) || 1;
      const result = await api.updateNotificationSubscriptions({
        subscriptions,
        task_overdue_interval_hours: intervalHours,
        task_overdue_daily_time_msk: taskOverdueDailyTimeMsk,
      });
      setSubscriptions(result.subscriptions);
      setTaskOverdueIntervalHours(String(result.task_overdue_interval_hours ?? 1));
      setTaskOverdueDailyTimeMsk(result.task_overdue_daily_time_msk ?? "09:00");
      toastSuccess("Подписки сохранены");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Ошибка сохранения";
      setError(msg);
      toastError(msg);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-2xl border border-border/60 bg-card p-6 space-y-4">
        <Skeleton className="h-6 w-48" />
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-14 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  const taskEvents = Object.entries(EVENT_TYPES).filter(
    ([, c]) => c.group === "tasks"
  );
  const meetingEvents = Object.entries(EVENT_TYPES).filter(
    ([, c]) => c.group === "meetings"
  );
  const overdueSubscriptionEnabled = subscriptions.task_overdue || false;
  const isDailyInterval = taskOverdueIntervalHours === "24";

  return (
    <div className="rounded-2xl border border-border/60 bg-card overflow-hidden">
      {/* Section header */}
      <div className="flex items-center gap-3 p-6 pb-0">
        <div className="h-9 w-9 rounded-xl bg-accent/10 flex items-center justify-center">
          <Bell className="h-5 w-5 text-accent" />
        </div>
        <div>
          <h2 className="font-heading font-semibold text-base">
            Подписки на уведомления
          </h2>
          <p className="text-xs text-muted-foreground">
            Получайте уведомления в Telegram при наступлении событий
          </p>
        </div>
      </div>

      <div className="p-6 space-y-5">
        {/* Task events */}
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground/70 mb-3">
            Задачи
          </p>
          <div className="space-y-1">
            {taskEvents.map(([eventType, config]) => {
              const Icon = config.icon;
              return (
                <div
                  key={eventType}
                  className="flex items-center gap-3 rounded-xl px-3 py-3 hover:bg-muted/40"
                >
                  <Icon className="h-4 w-4 text-muted-foreground shrink-0" />
                  <div className="flex-1 min-w-0">
                    <Label
                      htmlFor={`notify-${eventType}`}
                      className="cursor-pointer text-sm font-medium"
                    >
                      {config.label}
                    </Label>
                    <p className="text-2xs text-muted-foreground">
                      {config.description}
                    </p>
                  </div>
                  <Switch
                    id={`notify-${eventType}`}
                    checked={subscriptions[eventType] || false}
                    onCheckedChange={() => handleToggle(eventType)}
                  />
                </div>
              );
            })}
          </div>
        </div>

        <div className="rounded-xl border border-border/60 bg-muted/20 p-3">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <p className="text-sm font-medium">Периодичность напоминаний о просроченных задачах</p>
              <p className="text-2xs text-muted-foreground">
                По МСК: каждый час в начале часа или раз в сутки в выбранное время.
              </p>
            </div>
            <Select
              value={taskOverdueIntervalHours}
              onValueChange={setTaskOverdueIntervalHours}
              disabled={!overdueSubscriptionEnabled}
            >
              <SelectTrigger className="h-9 w-full rounded-lg sm:w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TASK_OVERDUE_INTERVAL_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {isDailyInterval && (
            <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-2xs text-muted-foreground">
                Время ежедневной отправки (МСК)
              </p>
              <TimePicker
                value={taskOverdueDailyTimeMsk}
                onChange={setTaskOverdueDailyTimeMsk}
                disabled={!overdueSubscriptionEnabled}
                className="h-9 w-full rounded-lg sm:w-40"
              />
            </div>
          )}
          {!overdueSubscriptionEnabled && (
            <p className="mt-2 text-2xs text-muted-foreground">
              Включите переключатель «Просроченная задача», чтобы применять периодичность.
            </p>
          )}
        </div>

        {/* Divider */}
        <div className="h-px bg-border/60" />

        {/* Meeting events */}
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground/70 mb-3">
            Встречи
          </p>
          <div className="space-y-1">
            {meetingEvents.map(([eventType, config]) => {
              const Icon = config.icon;
              return (
                <div
                  key={eventType}
                  className="flex items-center gap-3 rounded-xl px-3 py-3 hover:bg-muted/40"
                >
                  <Icon className="h-4 w-4 text-muted-foreground shrink-0" />
                  <div className="flex-1 min-w-0">
                    <Label
                      htmlFor={`notify-${eventType}`}
                      className="cursor-pointer text-sm font-medium"
                    >
                      {config.label}
                    </Label>
                    <p className="text-2xs text-muted-foreground">
                      {config.description}
                    </p>
                  </div>
                  <Switch
                    id={`notify-${eventType}`}
                    checked={subscriptions[eventType] || false}
                    onCheckedChange={() => handleToggle(eventType)}
                  />
                </div>
              );
            })}
          </div>
        </div>

        {error && (
          <div className="rounded-xl bg-destructive/10 border border-destructive/20 p-3">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        <Button
          onClick={handleSave}
          disabled={saving}
          className="w-full rounded-xl"
        >
          {saving ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Сохранение...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              Сохранить подписки
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
