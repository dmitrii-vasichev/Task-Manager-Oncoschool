"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Zap,
  CheckCircle2,
  AlertTriangle,
  CalendarDays,
  ArrowRight,
  Mic,
  FileText,
  Clock,
  UserX,
  AlertOctagon,
  Video,
  ExternalLink,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { PriorityBadge } from "@/components/shared/PriorityBadge";
import { UserAvatar } from "@/components/shared/UserAvatar";
import { EmptyState } from "@/components/shared/EmptyState";
import { useToast } from "@/components/shared/Toast";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { useDepartments } from "@/hooks/useDepartments";
import { PermissionService } from "@/lib/permissions";
import { getAccessibleDepartments } from "@/lib/departmentAccess";
import { api } from "@/lib/api";
import { UpcomingBirthdays } from "./team/components/UpcomingBirthdays";
import type {
  DashboardTasksAnalytics,
  MeetingAnalytics,
  OverviewAnalytics,
  Task,
  Meeting,
  TeamMember,
} from "@/lib/types";
import { parseLocalDate, parseUTCDate } from "@/lib/dateUtils";

// ────────────────────────────────────────────
// Helpers
// ────────────────────────────────────────────

function formatDate(dateStr: string): string {
  return parseLocalDate(dateStr).toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
  });
}

function formatFullDate(date: Date): string {
  return date.toLocaleDateString("ru-RU", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

function pluralizeRu(count: number, one: string, few: string, many: string): string {
  const normalized = Math.abs(count) % 100;
  const lastDigit = normalized % 10;
  if (normalized > 10 && normalized < 20) return many;
  if (lastDigit > 1 && lastDigit < 5) return few;
  if (lastDigit === 1) return one;
  return many;
}

function isOverdue(task: Task): boolean {
  if (!task.deadline || task.status === "done" || task.status === "cancelled")
    return false;
  const todayStart = new Date();
  todayStart.setHours(0, 0, 0, 0);
  return parseLocalDate(task.deadline) < todayStart;
}

function isStale(task: Task): boolean {
  const threeDaysAgo = new Date();
  threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);
  return new Date(task.updated_at) < threeDaysAgo;
}

function getDaysUntil(dateStr: string): number {
  const target = parseLocalDate(dateStr);
  target.setHours(0, 0, 0, 0);

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  return Math.round((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
}

function isDueSoon(task: Task, days: number = 2): boolean {
  if (!task.deadline || task.status === "done" || task.status === "cancelled") {
    return false;
  }
  const daysUntil = getDaysUntil(task.deadline);
  return daysUntil >= 0 && daysUntil <= days;
}

function getTaskPriorityWeight(priority: Task["priority"]): number {
  switch (priority) {
    case "urgent":
      return 400;
    case "high":
      return 240;
    case "medium":
      return 120;
    case "low":
    default:
      return 40;
  }
}

function getTaskFocusScore(task: Task): number {
  let score = getTaskPriorityWeight(task.priority);

  if (isOverdue(task)) {
    score += 1000;
  } else if (task.deadline) {
    const daysUntil = getDaysUntil(task.deadline);
    if (daysUntil === 0) score += 500;
    else if (daysUntil === 1) score += 380;
    else if (daysUntil <= 3) score += 240;
  }

  if (task.status === "review") score += 220;
  if (!task.assignee_id) score += 180;
  if (isStale(task)) score += 140;

  return score;
}

function firstName(fullName: string): string {
  return fullName.split(" ")[0] || fullName;
}

function firstAndLastName(fullName: string): string {
  const parts = fullName.trim().split(/\s+/).filter(Boolean);
  if (parts.length <= 2) return parts.join(" ");
  return `${parts[0]} ${parts[1]}`;
}

function getGreetingMessage(activeTasks: number, overdue: number): string {
  if (overdue > 0) {
    return `${overdue} ${pluralizeRu(overdue, "просроченная задача", "просроченные задачи", "просроченных задач")} — пора разобраться`;
  }
  if (activeTasks === 0) {
    return "Все задачи выполнены. Отличная работа!";
  }
  const messages = [
    `У тебя ${activeTasks} ${pluralizeRu(activeTasks, "задача", "задачи", "задач")} в работе`,
    `${activeTasks} ${pluralizeRu(activeTasks, "активная задача", "активные задачи", "активных задач")} — отличный день для прогресса`,
    `Впереди ${activeTasks} ${pluralizeRu(activeTasks, "задача", "задачи", "задач")}. Ты справишься!`,
  ];
  return messages[new Date().getDate() % messages.length];
}

// ────────────────────────────────────────────
// Metric Card
// ────────────────────────────────────────────

interface MetricCardProps {
  label: string;
  value: number;
  subtitle: string;
  icon: React.ElementType;
  accentColor: string;
  isPulsing?: boolean;
  staggerClass: string;
}

function MetricCard({
  label,
  value,
  subtitle,
  icon: Icon,
  accentColor,
  isPulsing,
  staggerClass,
}: MetricCardProps) {
  return (
    <div
      className={`animate-fade-in-up ${staggerClass} group relative overflow-hidden rounded-2xl border border-border/60 bg-card p-5 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-primary/5`}
    >
      {/* Top accent bar */}
      <div
        className="absolute inset-x-0 top-0 h-1 opacity-80 group-hover:opacity-100"
        style={{ backgroundColor: accentColor }}
      />

      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
          <div className="flex items-baseline gap-2">
            <span className="animate-count-up text-3xl font-bold font-heading tracking-tight">
              {value}
            </span>
            {isPulsing && value > 0 && (
              <span className="animate-pulse-glow inline-flex h-2.5 w-2.5 rounded-full bg-destructive" />
            )}
          </div>
          <p className="text-xs text-muted-foreground">{subtitle}</p>
        </div>

        <div
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl opacity-70 group-hover:opacity-100"
          style={{ backgroundColor: `${accentColor}18` }}
        >
          <Icon className="h-5 w-5" style={{ color: accentColor }} />
        </div>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────
// Skeleton loading
// ────────────────────────────────────────────

function DashboardSkeleton() {
  return (
    <div className="space-y-8">
      {/* Greeting skeleton */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-72" />
      </div>

      {/* Metric cards skeleton */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="rounded-2xl border border-border/60 bg-card p-5 space-y-3">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-9 w-16" />
            <Skeleton className="h-3 w-32" />
          </div>
        ))}
      </div>

      {/* Two-column skeleton */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-border/60 bg-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <Skeleton className="h-5 w-28" />
            <Skeleton className="h-8 w-24" />
          </div>
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-16 rounded-lg" />
          ))}
        </div>
        <div className="rounded-2xl border border-border/60 bg-card p-6 space-y-4">
          <Skeleton className="h-5 w-36" />
          <Skeleton className="h-24 rounded-lg" />
        </div>
      </div>

      {/* Meetings skeleton */}
      <div className="rounded-2xl border border-border/60 bg-card p-6">
        <Skeleton className="mb-4 h-5 w-40" />
        <div className="grid gap-4 md:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────
// Task list item (compact)
// ────────────────────────────────────────────

function TaskListItem({
  task,
  variant = "default",
  showAssignee = false,
}: {
  task: Task;
  variant?: "default" | "overdue" | "unassigned" | "stale";
  showAssignee?: boolean;
}) {
  const overdue = variant === "overdue" || isOverdue(task);
  const borderClass = overdue
    ? "border-destructive/35 bg-destructive/[0.06] hover:bg-destructive/[0.1] shadow-[0_0_0_1px_hsl(var(--destructive)/0.12)_inset]"
    : variant === "unassigned"
      ? "border-dashed border-muted-foreground/20 hover:bg-secondary/50"
      : variant === "stale"
        ? "border-amber-500/25 bg-amber-500/[0.03] hover:bg-amber-500/[0.07]"
        : "border hover:bg-secondary/50";

  const sourceIcon =
    task.source === "voice" ? (
      <Mic className="h-3 w-3 text-muted-foreground" />
    ) : task.source === "summary" ? (
      <FileText className="h-3 w-3 text-muted-foreground" />
    ) : null;

  return (
    <Link
      href={`/tasks/${task.short_id}`}
      className={`flex items-center gap-3 rounded-lg p-3 transition-all duration-150 ${borderClass}`}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground font-mono shrink-0">
            #{task.short_id}
          </span>
          {sourceIcon}
          <span
            className={`text-sm font-medium truncate ${
              overdue ? "text-destructive" : ""
            }`}
          >
            {task.title}
          </span>
        </div>
        <div className="mt-1.5 flex items-center gap-2 flex-wrap">
          {overdue && (
            <span className="inline-flex items-center rounded-full bg-destructive/12 px-2 py-0.5 text-[11px] font-medium text-destructive">
              Просрочено
            </span>
          )}
          <StatusBadge status={task.status} />
          <PriorityBadge priority={task.priority} />
          {task.deadline && (
            <span
              className={`text-xs flex items-center gap-1 ${
                overdue ? "text-destructive font-medium" : "text-muted-foreground"
              }`}
            >
              <CalendarDays className="h-3 w-3" />
              {formatDate(task.deadline)}
            </span>
          )}
          {variant === "unassigned" && task.created_by && (
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <UserAvatar name={task.created_by.full_name} avatarUrl={task.created_by.avatar_url} size="sm" />
              {task.created_by.full_name}
            </span>
          )}
          {variant === "stale" && (
            <span className="text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              Обновлено: {formatDate(task.updated_at)}
            </span>
          )}
          {showAssignee && (
            task.assignee ? (
              <span className="text-xs text-muted-foreground flex items-center gap-1 min-w-0">
                <UserAvatar
                  name={task.assignee.full_name}
                  avatarUrl={task.assignee.avatar_url}
                  size="sm"
                />
                <span className="truncate max-w-[150px]">
                  {firstAndLastName(task.assignee.full_name)}
                </span>
              </span>
            ) : (
              <span className="text-xs text-muted-foreground/70 flex items-center gap-1">
                <UserX className="h-3 w-3" />
                Не назначен
              </span>
            )
          )}
        </div>
      </div>
      <ArrowRight
        className={`h-4 w-4 shrink-0 ${overdue ? "text-destructive/45" : "text-muted-foreground/40"}`}
      />
    </Link>
  );
}

function CompactTaskLink({
  task,
  tone = "default",
}: {
  task: Task;
  tone?: "default" | "danger" | "warning";
}) {
  const toneClass =
    tone === "danger"
      ? "border-destructive/25 bg-destructive/[0.04] hover:bg-destructive/[0.08]"
      : tone === "warning"
        ? "border-amber-500/25 bg-amber-500/[0.03] hover:bg-amber-500/[0.06]"
        : "border-border/70 hover:bg-secondary/45";

  return (
    <Link
      href={`/tasks/${task.short_id}`}
      className={`flex items-center justify-between gap-3 rounded-lg border px-3 py-2 transition-colors ${toneClass}`}
    >
      <div className="min-w-0">
        <p className="text-[11px] font-mono text-muted-foreground">#{task.short_id}</p>
        <p className="truncate text-sm font-medium">{task.title}</p>
      </div>
      <ArrowRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground/50" />
    </Link>
  );
}

// ────────────────────────────────────────────
// Section header
// ────────────────────────────────────────────

function SectionHeader({
  title,
  icon: Icon,
  iconColor,
  linkHref,
  linkLabel,
  count,
}: {
  title: string;
  icon?: React.ElementType;
  iconColor?: string;
  linkHref?: string;
  linkLabel?: string;
  count?: number;
}) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-2">
        {Icon && (
          <Icon
            className="h-[18px] w-[18px]"
            style={iconColor ? { color: iconColor } : undefined}
          />
        )}
        <h2 className="text-base font-semibold font-heading">{title}</h2>
        {count !== undefined && count > 0 && (
          <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-muted px-1.5 text-xs font-medium text-muted-foreground">
            {count}
          </span>
        )}
      </div>
      {linkHref && (
        <Link
          href={linkHref}
          className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
        >
          {linkLabel || "Смотреть все"}
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      )}
    </div>
  );
}

// ────────────────────────────────────────────
// Upcoming meeting card (with Zoom link)
// ────────────────────────────────────────────

function UpcomingMeetingCard({
  meeting,
  staggerClass,
}: {
  meeting: Meeting;
  staggerClass: string;
}) {
  const meetingDate = meeting.meeting_date
    ? parseUTCDate(meeting.meeting_date)
    : null;

  const dateStr = meetingDate
    ? meetingDate.toLocaleDateString("ru-RU", {
        weekday: "short",
        day: "numeric",
        month: "short",
      })
    : "";

  const timeStr = meetingDate
    ? meetingDate.toLocaleTimeString("ru-RU", {
        hour: "2-digit",
        minute: "2-digit",
      })
    : "";

  return (
    <div
      className={`animate-fade-in-up ${staggerClass} group rounded-2xl border border-border/60 bg-card p-5 transition-shadow duration-200 hover:shadow-md hover:shadow-primary/5`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <Link
            href={`/meetings/${meeting.id}`}
            className="text-sm font-semibold truncate block group-hover:text-primary transition-colors"
          >
            {meeting.title || "Встреча без названия"}
          </Link>
          <p className="mt-1 text-xs text-muted-foreground flex items-center gap-1">
            <CalendarDays className="h-3 w-3 shrink-0" />
            {dateStr} · {timeStr}
          </p>
        </div>
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400">
          <Video className="h-4 w-4" />
        </div>
      </div>
      {meeting.zoom_join_url && (
        <a
          href={meeting.zoom_join_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 flex items-center gap-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline"
        >
          <ExternalLink className="h-3 w-3" />
          Подключиться к Zoom
        </a>
      )}
    </div>
  );
}

// ────────────────────────────────────────────
// Meeting card (past)
// ────────────────────────────────────────────

function MeetingCard({
  meeting,
  staggerClass,
}: {
  meeting: Meeting;
  staggerClass: string;
}) {
  const meetingDate = meeting.meeting_date
    ? parseUTCDate(meeting.meeting_date).toLocaleDateString("ru-RU", {
        day: "numeric",
        month: "short",
      })
    : parseUTCDate(meeting.created_at).toLocaleDateString("ru-RU", {
        day: "numeric",
        month: "short",
      });

  return (
    <Link
      href={`/meetings/${meeting.id}`}
      className={`animate-fade-in-up ${staggerClass} group block rounded-2xl border border-border/60 bg-card p-5 transition-shadow duration-200 hover:shadow-md hover:shadow-primary/5`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold truncate group-hover:text-primary transition-colors">
            {meeting.title || "Встреча без названия"}
          </p>
          <p className="mt-1 text-xs text-muted-foreground flex items-center gap-1">
            <CalendarDays className="h-3 w-3 shrink-0" />
            {meetingDate}
          </p>
          {meeting.decisions && meeting.decisions.length > 0 && (
            <p className="mt-2 text-xs text-muted-foreground line-clamp-2">
              {meeting.decisions[0]}
            </p>
          )}
        </div>
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <FileText className="h-4 w-4" />
        </div>
      </div>
    </Link>
  );
}

// ────────────────────────────────────────────
// Main Dashboard
// ────────────────────────────────────────────

export default function DashboardPage() {
  const { user } = useCurrentUser();
  const { departments, loading: departmentsLoading } = useDepartments();
  const { toastError } = useToast();
  const [loading, setLoading] = useState(true);

  // Data
  const [dashboardTasksAnalytics, setDashboardTasksAnalytics] =
    useState<DashboardTasksAnalytics | null>(null);
  const [meetingAnalytics, setMeetingAnalytics] =
    useState<MeetingAnalytics | null>(null);
  const [overview, setOverview] = useState<OverviewAnalytics | null>(null);
  const [myTasks, setMyTasks] = useState<Task[]>([]);
  const [departmentTasks, setDepartmentTasks] = useState<Task[]>([]);
  const [selectedDepartmentId, setSelectedDepartmentId] = useState("");
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [upcomingMeetings, setUpcomingMeetings] = useState<Meeting[]>([]);
  const [unassignedTasks, setUnassignedTasks] = useState<Task[]>([]);
  const [staleTasks, setStaleTasks] = useState<Task[]>([]);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);

  const isModerator = user ? PermissionService.isModerator(user) : false;
  const userId = user?.id || "";
  const userDepartmentId = user?.department_id || "";
  const userRole = user?.role || "";

  const accessibleDepartments = useMemo(
    () =>
      getAccessibleDepartments({
        departments,
        userId,
        userRole,
        userDepartmentId: userDepartmentId || null,
      }),
    [departments, userDepartmentId, userId, userRole]
  );
  const canSwitchDepartment = isModerator || accessibleDepartments.length > 1;

  useEffect(() => {
    if (!userId || departmentsLoading) return;

    setSelectedDepartmentId((current) => {
      const availableIds = new Set(accessibleDepartments.map((d) => d.id));

      if (isModerator) {
        if (!current) return "";
        return availableIds.has(current) ? current : "";
      }

      if (current && availableIds.has(current)) {
        return current;
      }
      if (userDepartmentId && availableIds.has(userDepartmentId)) {
        return userDepartmentId;
      }
      return accessibleDepartments[0]?.id || "";
    });
  }, [accessibleDepartments, departmentsLoading, isModerator, userDepartmentId, userId]);

  const selectedDepartment = useMemo(
    () =>
      departments.find((department) => department.id === selectedDepartmentId) || null,
    [departments, selectedDepartmentId]
  );

  const isDepartmentHead =
    Boolean(userId && selectedDepartment && selectedDepartment.head_id === userId);
  const dashboardRole: "employee" | "lead" | "moderator" = isModerator
    ? "moderator"
    : isDepartmentHead
      ? "lead"
      : "employee";

  useEffect(() => {
    if (!userId || departmentsLoading) return;
    let cancelled = false;

    async function fetchData() {
      setLoading(true);
      try {
        const catchLog = (label: string) => (err: unknown) => {
          if (process.env.NODE_ENV === "development") {
            console.error(`[Dashboard] ${label} failed:`, err);
          }
          return null;
        };

        const openStatuses = "new,in_progress,review";
        const selectedDepartmentParam = selectedDepartmentId || undefined;
        const shouldLoadDepartmentTasks = Boolean(selectedDepartmentParam) || isModerator;
        const emptyTasksPage = {
          items: [] as Task[],
          total: 0,
          page: 1,
          per_page: 0,
          pages: 1,
        };

        const results = await Promise.all([
          api
            .getDashboardTasksAnalytics(selectedDepartmentParam)
            .catch(catchLog("getDashboardTasksAnalytics")),
          api.getMeetingsAnalytics().catch(catchLog("getMeetingsAnalytics")),
          api.getOverview(selectedDepartmentParam).catch(catchLog("getOverview")),
          api
            .getTasks({
              assignee_id: userId,
              ...(selectedDepartmentParam
                ? { department_id: selectedDepartmentParam }
                : {}),
              status: openStatuses,
              per_page: "50",
              sort: "created_at_desc",
            })
            .catch(catchLog("getMyTasks")),
          shouldLoadDepartmentTasks
            ? api
                .getTasks({
                  ...(selectedDepartmentParam
                    ? { department_id: selectedDepartmentParam }
                    : {}),
                  status: openStatuses,
                  per_page: "50",
                  sort: "created_at_desc",
                })
                .catch(catchLog("getDepartmentTasks"))
            : Promise.resolve(emptyTasksPage),
          api.getMeetings({ upcoming: true }).catch(catchLog("getUpcomingMeetings")),
          api.getMeetings({ past: true }).catch(catchLog("getPastMeetings")),
          api.getTeam().catch(catchLog("getTeam")),
          isModerator
            ? api
                .getTasks({
                  status: "new",
                  per_page: "100",
                  sort: "created_at_desc",
                })
                .catch(catchLog("getUnassignedTasks"))
            : Promise.resolve(emptyTasksPage),
          isModerator
            ? api
                .getTasks({
                  status: "in_progress,review",
                  per_page: "100",
                  sort: "created_at_asc",
                })
                .catch(catchLog("getStaleTasks"))
            : Promise.resolve(emptyTasksPage),
        ]);

        if (cancelled) return;

        const dashboardData = results[0] as DashboardTasksAnalytics | null;
        const meetingData = results[1] as MeetingAnalytics | null;
        const overviewData = results[2] as OverviewAnalytics | null;
        const myTasksData = results[3] as { items: Task[] } | null;
        const departmentTasksData = results[4] as { items: Task[] } | null;
        const upcomingData = results[5] as Meeting[] | null;
        const pastData = results[6] as Meeting[] | null;
        const teamData = results[7] as TeamMember[] | null;
        const unassignedData = results[8] as { items: Task[] } | null;
        const staleData = results[9] as { items: Task[] } | null;

        const hasError = results.some((r) => r === null);

        setDashboardTasksAnalytics(dashboardData);
        setMeetingAnalytics(meetingData);
        setOverview(overviewData);
        setTeamMembers(teamData ?? []);

        setMyTasks(myTasksData?.items ?? []);
        setDepartmentTasks(departmentTasksData?.items ?? []);

        // Upcoming meetings (top 3)
        setUpcomingMeetings(upcomingData ? upcomingData.slice(0, 3) : []);

        // Recent past meetings (top 3)
        setMeetings(pastData ? pastData.slice(0, 3) : []);

        // Moderator data
        if (isModerator) {
          setUnassignedTasks(
            unassignedData
              ? unassignedData.items.filter((t) => !t.assignee_id)
              : []
          );
          setStaleTasks(staleData ? staleData.items.filter(isStale) : []);
        } else {
          setUnassignedTasks([]);
          setStaleTasks([]);
        }

        if (hasError) toastError("Не удалось загрузить часть данных");
      } catch {
        if (!cancelled) toastError("Не удалось загрузить данные");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchData();
    return () => {
      cancelled = true;
    };
  }, [departmentsLoading, isModerator, selectedDepartmentId, toastError, userId]);

  if (!user) return null;

  if (loading || departmentsLoading) {
    return <DashboardSkeleton />;
  }

  const myMetrics = dashboardTasksAnalytics?.my;
  const departmentMetrics = dashboardTasksAnalytics?.department;

  const departmentOverdueTasks = departmentTasks.filter(isOverdue);

  const dueSoonMyCount = myTasks.filter((task) => isDueSoon(task)).length;
  const dueSoonDepartmentCount = departmentTasks.filter((task) => isDueSoon(task)).length;
  const unassignedDepartmentCount = departmentTasks.filter((task) => !task.assignee_id)
    .length;

  const employeeFocusTasks = [...myTasks]
    .sort((a, b) => getTaskFocusScore(b) - getTaskFocusScore(a))
    .slice(0, 5);

  const leadFocusTasks = [...departmentTasks]
    .filter(
      (task) =>
        isOverdue(task) ||
        isDueSoon(task, 1) ||
        task.status === "review" ||
        !task.assignee_id ||
        isStale(task)
    )
    .sort((a, b) => getTaskFocusScore(b) - getTaskFocusScore(a))
    .slice(0, 5);

  const moderatorFocusDepartments = [...(overview?.departments ?? [])]
    .filter((row) => row.active_tasks > 0 || row.overdue_tasks > 0)
    .sort((a, b) => {
      if (b.overdue_tasks !== a.overdue_tasks) {
        return b.overdue_tasks - a.overdue_tasks;
      }
      return b.active_tasks - a.active_tasks;
    })
    .slice(0, 3);

  const teamLoadMap = new Map<
    string,
    {
      id: string;
      fullName: string;
      avatarUrl: string | null;
      total: number;
      overdue: number;
      review: number;
    }
  >();

  for (const task of departmentTasks) {
    if (!task.assignee_id || !task.assignee) continue;
    const existing = teamLoadMap.get(task.assignee_id) ?? {
      id: task.assignee_id,
      fullName: task.assignee.full_name,
      avatarUrl: task.assignee.avatar_url,
      total: 0,
      overdue: 0,
      review: 0,
    };
    existing.total += 1;
    if (isOverdue(task)) existing.overdue += 1;
    if (task.status === "review") existing.review += 1;
    teamLoadMap.set(task.assignee_id, existing);
  }

  const teamLoadRows = Array.from(teamLoadMap.values())
    .sort((a, b) => {
      if (b.overdue !== a.overdue) return b.overdue - a.overdue;
      if (b.total !== a.total) return b.total - a.total;
      return b.review - a.review;
    })
    .slice(0, 4);

  const primaryMetrics = dashboardRole === "employee" ? myMetrics : departmentMetrics;
  const activeTasks = primaryMetrics?.active ?? 0;
  const overdueCount = primaryMetrics?.overdue ?? 0;
  const reviewCount = primaryMetrics?.review ?? 0;
  const doneWeekCount = primaryMetrics?.done_week ?? 0;
  const inProgressCount = primaryMetrics?.in_progress ?? 0;

  const todayStr = formatFullDate(new Date());
  const greeting = getGreetingMessage(activeTasks, overdueCount);
  const hasOverdueTasks = overdueCount > 0;
  const overdueSummary = `${overdueCount} ${pluralizeRu(overdueCount, "просроченная задача", "просроченные задачи", "просроченных задач")}`;
  const activeSummary = `${activeTasks} ${pluralizeRu(activeTasks, "задача", "задачи", "задач")} в работе`;
  const buildTasksHref = (preset: "kanban" | "backlog" | "overdue"): string => {
    const params = new URLSearchParams({ preset });
    if (selectedDepartmentId) {
      params.set("department_id", selectedDepartmentId);
    }
    return `/tasks?${params.toString()}`;
  };
  const kanbanHref = buildTasksHref("kanban");
  const backlogHref = buildTasksHref("backlog");
  const overdueHref = buildTasksHref("overdue");

  // Accent colors mapped to design system
  const ACCENT_PRIMARY = "hsl(174, 62%, 26%)";
  const ACCENT_DONE = "hsl(152, 55%, 28%)";
  const ACCENT_DESTRUCTIVE = "hsl(0, 72%, 51%)";
  const ACCENT_BLUE = "hsl(200, 65%, 48%)";
  const ACCENT_AMBER = "hsl(38, 80%, 52%)";

  const roleTitle =
    dashboardRole === "moderator"
      ? "Операционный дашборд модератора"
      : dashboardRole === "lead"
        ? "Операционный дашборд руководителя"
        : "Личный операционный дашборд";
  const scopeLabel = selectedDepartment
    ? `Срез по отделу: ${selectedDepartment.name}`
    : isModerator
      ? "Срез по всем отделам"
      : "Личный срез";
  const roleHint =
    dashboardRole === "moderator"
      ? "Сначала очереди риска, затем распределение нагрузки между отделами."
      : dashboardRole === "lead"
        ? "Приоритет: просрочки и задачи без owner внутри отдела."
        : "Приоритет: закрыть просрочки и задачи с ближайшим дедлайном.";

  const riskCards: Array<{
    label: string;
    value: number;
    subtitle: string;
    icon: React.ElementType;
    accentColor: string;
    isPulsing?: boolean;
  }> =
    dashboardRole === "employee"
      ? [
          {
            label: "Просрочено",
            value: myMetrics?.overdue ?? 0,
            subtitle: `${myMetrics?.active ?? 0} активных`,
            icon: AlertTriangle,
            accentColor: ACCENT_DESTRUCTIVE,
            isPulsing: true,
          },
          {
            label: "Дедлайн ≤2 дней",
            value: dueSoonMyCount,
            subtitle: "Личный контур",
            icon: Clock,
            accentColor: ACCENT_AMBER,
          },
          {
            label: "На ревью",
            value: myMetrics?.review ?? 0,
            subtitle: "Требуют завершения",
            icon: FileText,
            accentColor: ACCENT_PRIMARY,
          },
          {
            label: "Done за неделю",
            value: myMetrics?.done_week ?? 0,
            subtitle: `Всего done: ${myMetrics?.done_total ?? 0}`,
            icon: CheckCircle2,
            accentColor: ACCENT_DONE,
          },
        ]
      : dashboardRole === "lead"
        ? [
            {
              label: "Просрочено в отделе",
              value: departmentMetrics?.overdue ?? 0,
              subtitle: `${departmentMetrics?.active ?? 0} активных`,
              icon: AlertTriangle,
              accentColor: ACCENT_DESTRUCTIVE,
              isPulsing: true,
            },
            {
              label: "Без исполнителя",
              value: unassignedDepartmentCount,
              subtitle: "Требуют owner",
              icon: UserX,
              accentColor: ACCENT_AMBER,
            },
            {
              label: "Очередь ревью",
              value: departmentMetrics?.review ?? 0,
              subtitle: `${dueSoonDepartmentCount} дедлайн ≤2 дней`,
              icon: FileText,
              accentColor: ACCENT_PRIMARY,
            },
            {
              label: "Done за неделю",
              value: departmentMetrics?.done_week ?? 0,
              subtitle: `Всего done: ${departmentMetrics?.done_total ?? 0}`,
              icon: CheckCircle2,
              accentColor: ACCENT_DONE,
            },
          ]
        : [
            {
              label: "Просрочено",
              value: departmentMetrics?.overdue ?? 0,
              subtitle: `${departmentMetrics?.active ?? 0} активных`,
              icon: AlertTriangle,
              accentColor: ACCENT_DESTRUCTIVE,
              isPulsing: true,
            },
            {
              label: "Без исполнителя",
              value: unassignedTasks.length,
              subtitle: "Новые задачи без owner",
              icon: UserX,
              accentColor: ACCENT_AMBER,
            },
            {
              label: "Не обновлялись >3 дней",
              value: staleTasks.length,
              subtitle: "В работе и ревью",
              icon: AlertOctagon,
              accentColor: ACCENT_PRIMARY,
            },
            {
              label: "Встреч за месяц",
              value: meetingAnalytics?.meetings_this_month ?? 0,
              subtitle: `Всего встреч: ${meetingAnalytics?.total_meetings ?? 0}`,
              icon: CalendarDays,
              accentColor: ACCENT_BLUE,
            },
          ];

  const focusTasks = dashboardRole === "employee" ? employeeFocusTasks : leadFocusTasks;
  const focusTitle =
    dashboardRole === "employee" ? "Фокус: мои задачи" : "Проблемные задачи отдела";
  const focusEmptyTitle =
    dashboardRole === "employee"
      ? "Нет задач в фокусе"
      : "Сильных рисков по отделу сейчас нет";
  const focusEmptyDescription =
    dashboardRole === "employee"
      ? "Все текущие задачи в стабильной зоне."
      : "Просрочки и очереди ревью под контролем.";

  const nextMeeting = upcomingMeetings[0] ?? null;
  const nextMeetingDateLabel =
    nextMeeting?.meeting_date
      ? parseUTCDate(nextMeeting.meeting_date).toLocaleDateString("ru-RU", {
          weekday: "short",
          day: "numeric",
          month: "short",
        })
      : null;
  const nextMeetingTimeLabel =
    nextMeeting?.meeting_date
      ? parseUTCDate(nextMeeting.meeting_date).toLocaleTimeString("ru-RU", {
          hour: "2-digit",
          minute: "2-digit",
        })
      : null;

  return (
    <div className="space-y-6">
      {/* ═══════════ Header / Scope ═══════════ */}
      <section className="animate-fade-in-up stagger-1">
        <div
          className={`rounded-2xl border p-4 md:p-5 ${
            hasOverdueTasks
              ? "border-destructive/25 bg-destructive/[0.03]"
              : "border-border/60 bg-card"
          }`}
        >
          <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
            <div className="min-w-0">
              <h1 className="text-xl font-bold font-heading tracking-tight md:text-2xl">
                Привет, {firstName(user.full_name)}!
              </h1>
              <p className="mt-1 text-sm font-medium text-foreground">{roleTitle}</p>
              <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
                <span className="capitalize">{todayStr}</span>
                <span className="text-border">•</span>
                <span>{scopeLabel}</span>
              </p>
              <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground md:text-sm">
                {hasOverdueTasks ? (
                  <span className="inline-flex items-center gap-1 font-medium text-destructive">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    {overdueSummary}
                  </span>
                ) : (
                  <span>{greeting}</span>
                )}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">{activeSummary}</p>
              <p className="mt-1 text-xs text-muted-foreground">{roleHint}</p>
            </div>

            <div className="flex w-full flex-wrap items-center gap-2 xl:w-auto xl:justify-end">
              {hasOverdueTasks ? (
                <Button asChild size="sm" variant="destructive" className="sm:shrink-0">
                  <Link href={overdueHref}>Разобрать просрочки</Link>
                </Button>
              ) : (
                <Button asChild size="sm" variant="secondary" className="sm:shrink-0">
                  <Link href={backlogHref}>
                    Весь бэклог
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </Button>
              )}
              <Button
                asChild
                size="sm"
                variant="ghost"
                className="sm:shrink-0 text-muted-foreground hover:text-foreground"
              >
                <Link href={kanbanHref}>
                  Канбан-доска
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </Button>

              {canSwitchDepartment && (
                <div className="flex h-9 w-full min-w-[240px] items-center gap-2 rounded-md border border-border/60 bg-background px-2 shadow-sm sm:w-[280px]">
                  <span className="pl-1 text-xs font-medium text-muted-foreground">
                    Отдел
                  </span>
                  <Select
                    value={
                      isModerator
                        ? selectedDepartmentId || "__all__"
                        : selectedDepartmentId ||
                          (accessibleDepartments[0]?.id
                            ? accessibleDepartments[0].id
                            : "__none__")
                    }
                    onValueChange={(value) => {
                      if (value === "__none__") return;
                      if (value === "__all__") {
                        setSelectedDepartmentId("");
                        return;
                      }
                      setSelectedDepartmentId(value);
                    }}
                  >
                    <SelectTrigger className="h-8 flex-1 border-0 bg-transparent px-2 shadow-none focus:ring-0">
                      <SelectValue placeholder="Выберите отдел" />
                    </SelectTrigger>
                    <SelectContent>
                      {accessibleDepartments.length === 0 && !isModerator ? (
                        <SelectItem value="__none__" disabled>
                          Нет доступных отделов
                        </SelectItem>
                      ) : (
                        <>
                          {isModerator && (
                            <SelectItem value="__all__">Все отделы</SelectItem>
                          )}
                          {accessibleDepartments.map((department) => (
                            <SelectItem key={department.id} value={department.id}>
                              {department.name}
                            </SelectItem>
                          ))}
                        </>
                      )}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════ Risk Metrics ═══════════ */}
      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {riskCards.map((card, index) => (
          <MetricCard
            key={card.label}
            label={card.label}
            value={card.value}
            subtitle={card.subtitle}
            icon={card.icon}
            accentColor={card.accentColor}
            isPulsing={card.isPulsing}
            staggerClass={`stagger-${Math.min(index + 2, 8)}`}
          />
        ))}
      </section>

      {/* ═══════════ Role Main Zone ═══════════ */}
      <section className="animate-fade-in-up stagger-6">
        <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
          <div className="rounded-2xl border border-border/60 bg-card p-6">
            {dashboardRole === "moderator" ? (
              <>
                <SectionHeader
                  title="Отделы в зоне риска"
                  icon={AlertTriangle}
                  iconColor={ACCENT_DESTRUCTIVE}
                  count={moderatorFocusDepartments.length}
                  linkHref="/analytics"
                  linkLabel="Расширенная аналитика"
                />

                {moderatorFocusDepartments.length === 0 ? (
                  <EmptyState
                    variant="tasks"
                    title="Критичных сигналов по отделам нет"
                    description="Просрочки и загрузка в допустимых границах."
                    className="py-6"
                  />
                ) : (
                  <div className="space-y-2">
                    {moderatorFocusDepartments.map((row) => {
                      const params = new URLSearchParams({
                        preset: "overdue",
                        department_id: row.department_id,
                      });
                      return (
                        <Link
                          key={row.department_id}
                          href={`/tasks?${params.toString()}`}
                          className="flex items-center justify-between gap-3 rounded-xl border border-border/70 px-4 py-3 transition-colors hover:bg-secondary/40"
                        >
                          <div className="min-w-0">
                            <p className="flex items-center gap-2 text-sm font-medium">
                              <span
                                className="h-2.5 w-2.5 rounded-full"
                                style={{
                                  backgroundColor:
                                    row.department_color || "hsl(var(--muted-foreground))",
                                }}
                              />
                              <span className="truncate">{row.department_name}</span>
                            </p>
                            <p className="mt-1 text-xs text-muted-foreground">
                              {row.active_tasks} активных · {row.done_week} done за неделю
                            </p>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-xs font-medium text-destructive">
                              {row.overdue_tasks} просроч.
                            </span>
                            <ArrowRight className="h-3.5 w-3.5 text-muted-foreground/50" />
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                )}
              </>
            ) : (
              <>
                <SectionHeader
                  title={focusTitle}
                  count={focusTasks.length}
                  linkHref="/tasks"
                  linkLabel="Смотреть все"
                />

                {focusTasks.length === 0 ? (
                  <EmptyState
                    variant="tasks"
                    title={focusEmptyTitle}
                    description={focusEmptyDescription}
                    className="py-6"
                  />
                ) : (
                  <div className="space-y-2">
                    {focusTasks.map((task) => (
                      <TaskListItem
                        key={task.id}
                        task={task}
                        variant={
                          isOverdue(task)
                            ? "overdue"
                            : !task.assignee_id
                              ? "unassigned"
                              : isStale(task)
                                ? "stale"
                                : "default"
                        }
                        showAssignee={dashboardRole === "lead"}
                      />
                    ))}
                  </div>
                )}
              </>
            )}
          </div>

          <div className="rounded-2xl border border-border/60 bg-card p-6">
            {dashboardRole === "employee" && (
              <>
                <SectionHeader title="Сегодня" icon={Zap} iconColor={ACCENT_PRIMARY} />

                {nextMeeting ? (
                  <div className="rounded-xl border border-border/70 bg-background/60 p-4">
                    <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                      Следующая встреча
                    </p>
                    <p className="mt-1 truncate text-sm font-semibold">
                      {nextMeeting.title || "Встреча без названия"}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {nextMeetingDateLabel} · {nextMeetingTimeLabel}
                    </p>
                    {nextMeeting.zoom_join_url && (
                      <a
                        href={nextMeeting.zoom_join_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:underline"
                      >
                        <ExternalLink className="h-3 w-3" />
                        Подключиться к Zoom
                      </a>
                    )}
                  </div>
                ) : (
                  <div className="rounded-xl border border-dashed border-border/70 bg-background/40 p-4 text-xs text-muted-foreground">
                    На ближайшее время встреч не запланировано.
                  </div>
                )}

                <div className="mt-4 rounded-xl border border-border/70 bg-background/60 p-4">
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Контроль на день
                  </p>
                  <div className="mt-2 space-y-1.5 text-sm">
                    <p>Дедлайн ≤2 дней: {dueSoonMyCount}</p>
                    <p>В работе: {inProgressCount}</p>
                    <p>На ревью: {reviewCount}</p>
                    <p>Done за неделю: {doneWeekCount}</p>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <Button asChild size="sm" variant="secondary">
                    <Link href={overdueHref}>Разобрать просрочки</Link>
                  </Button>
                  <Button asChild size="sm" variant="ghost">
                    <Link href={kanbanHref}>Канбан</Link>
                  </Button>
                </div>
              </>
            )}

            {dashboardRole === "lead" && (
              <>
                <SectionHeader title="Нагрузка команды" icon={Zap} iconColor={ACCENT_PRIMARY} />

                <div className="rounded-xl border border-border/70 bg-background/60 p-4">
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Контроль отдела
                  </p>
                  <div className="mt-2 space-y-1.5 text-sm">
                    <p>Просрочено: {departmentOverdueTasks.length}</p>
                    <p>Без исполнителя: {unassignedDepartmentCount}</p>
                    <p>Очередь ревью: {departmentMetrics?.review ?? 0}</p>
                    <p>Дедлайн ≤2 дней: {dueSoonDepartmentCount}</p>
                  </div>
                </div>

                <div className="mt-4 space-y-2">
                  {teamLoadRows.length === 0 ? (
                    <div className="rounded-xl border border-dashed border-border/70 bg-background/40 p-4 text-xs text-muted-foreground">
                      По текущим задачам нет данных по загрузке команды.
                    </div>
                  ) : (
                    teamLoadRows.map((member) => (
                      <div
                        key={member.id}
                        className="flex items-center justify-between rounded-lg border border-border/70 px-3 py-2"
                      >
                        <div className="flex min-w-0 items-center gap-2">
                          <UserAvatar
                            name={member.fullName}
                            avatarUrl={member.avatarUrl}
                            size="sm"
                          />
                          <p className="truncate text-sm font-medium">
                            {firstAndLastName(member.fullName)}
                          </p>
                        </div>
                        <div className="text-right text-xs text-muted-foreground">
                          <p>{member.total} в работе</p>
                          <p className="text-destructive">{member.overdue} просроч.</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <Button asChild size="sm" variant="secondary">
                    <Link href={overdueHref}>Снять просрочки</Link>
                  </Button>
                  <Button asChild size="sm" variant="ghost">
                    <Link href={backlogHref}>Весь backlog</Link>
                  </Button>
                </div>
              </>
            )}

            {dashboardRole === "moderator" && (
              <>
                <SectionHeader
                  title="Операционные очереди"
                  icon={AlertOctagon}
                  iconColor={ACCENT_AMBER}
                />

                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-xl border border-border/70 bg-background/60 p-3">
                    <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                      Без исполнителя
                    </p>
                    <p className="mt-1 text-xl font-semibold">{unassignedTasks.length}</p>
                  </div>
                  <div className="rounded-xl border border-border/70 bg-background/60 p-3">
                    <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                      Не обновлялись
                    </p>
                    <p className="mt-1 text-xl font-semibold">{staleTasks.length}</p>
                  </div>
                </div>

                <div className="mt-4 space-y-3">
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-muted-foreground">
                      Без исполнителя (top 3)
                    </p>
                    {unassignedTasks.length === 0 ? (
                      <p className="text-xs text-muted-foreground">Пусто</p>
                    ) : (
                      unassignedTasks
                        .slice(0, 3)
                        .map((task) => (
                          <CompactTaskLink key={task.id} task={task} tone="danger" />
                        ))
                    )}
                  </div>

                  <div className="space-y-2">
                    <p className="text-xs font-medium text-muted-foreground">
                      Не обновлялись {'>'}3 дней (top 3)
                    </p>
                    {staleTasks.length === 0 ? (
                      <p className="text-xs text-muted-foreground">Пусто</p>
                    ) : (
                      staleTasks
                        .slice(0, 3)
                        .map((task) => (
                          <CompactTaskLink key={task.id} task={task} tone="warning" />
                        ))
                    )}
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <Button asChild size="sm" variant="secondary">
                    <Link href={overdueHref}>Просрочки</Link>
                  </Button>
                  <Button asChild size="sm" variant="ghost">
                    <Link href="/analytics">Аналитика</Link>
                  </Button>
                </div>
              </>
            )}
          </div>
        </div>
      </section>

      {/* ═══════════ Meetings (Compact) ═══════════ */}
      {(upcomingMeetings.length > 0 || meetings.length > 0) && (
        <section className="animate-fade-in-up stagger-7">
          <div className="rounded-2xl border border-border/60 bg-card p-6">
            <div className="grid gap-6 lg:grid-cols-2">
              <div>
                <SectionHeader
                  title="Ближайшие встречи"
                  icon={Video}
                  iconColor={ACCENT_BLUE}
                  linkHref="/meetings"
                  linkLabel="Все встречи"
                  count={upcomingMeetings.length}
                />
                {upcomingMeetings.length === 0 ? (
                  <div className="rounded-xl border border-dashed border-border/70 bg-background/40 p-4 text-xs text-muted-foreground">
                    Ближайших встреч нет.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {upcomingMeetings.slice(0, 2).map((meeting, i) => (
                      <UpcomingMeetingCard
                        key={meeting.id}
                        meeting={meeting}
                        staggerClass={`stagger-${Math.min(i + 7, 8)}`}
                      />
                    ))}
                  </div>
                )}
              </div>

              <div>
                <SectionHeader
                  title="Последние встречи"
                  icon={CalendarDays}
                  linkHref="/meetings"
                  linkLabel="Все встречи"
                  count={meetings.length}
                />
                {meetings.length === 0 ? (
                  <div className="rounded-xl border border-dashed border-border/70 bg-background/40 p-4 text-xs text-muted-foreground">
                    Завершённых встреч пока нет.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {meetings.slice(0, 2).map((meeting, i) => (
                      <MeetingCard
                        key={meeting.id}
                        meeting={meeting}
                        staggerClass={`stagger-${Math.min(i + 7, 8)}`}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* ═══════════ Birthdays ═══════════ */}
      {teamMembers.length > 0 && (
        <section className="animate-fade-in-up stagger-8">
          <UpcomingBirthdays members={teamMembers} className="" />
        </section>
      )}

    </div>
  );
}
