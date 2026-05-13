"use client";

import Link from "next/link";
import {
  ArrowRight,
  Building2,
  CalendarClock,
  Flag,
  Lightbulb,
  ListChecks,
  type LucideIcon,
} from "lucide-react";
import { ProjectStatusBadge } from "@/components/projects/ProjectStatusBadge";
import { UserAvatar } from "@/components/shared/UserAvatar";
import {
  formatProjectDepartmentProgress,
  formatProjectMilestoneProgress,
  formatProjectTaskProgress,
} from "@/lib/projectUtils";
import { parseUTCDate } from "@/lib/dateUtils";
import { cn } from "@/lib/utils";
import type { Project } from "@/lib/types";

function formatDate(value: string): string {
  const parsed = parseUTCDate(value);
  if (Number.isNaN(parsed.getTime())) return "Дата не указана";

  return parsed.toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

function MetaPill({
  icon: Icon,
  label,
  value,
  avatarName,
  avatarUrl,
}: {
  icon?: LucideIcon;
  label: string;
  value: string;
  avatarName?: string;
  avatarUrl?: string | null;
}) {
  return (
    <span className="inline-flex h-6 min-w-0 items-center gap-1.5 rounded-md bg-muted/60 px-2 text-xs text-muted-foreground">
      {avatarName ? (
        <UserAvatar name={avatarName} avatarUrl={avatarUrl || null} size="sm" />
      ) : Icon ? (
        <Icon className="h-3.5 w-3.5 shrink-0" />
      ) : null}
      <span className="shrink-0 font-medium text-muted-foreground">{label}:</span>
      <span className="truncate text-foreground">{value}</span>
    </span>
  );
}

function ProgressMetric({
  icon: Icon,
  label,
  tone,
}: {
  icon: LucideIcon;
  label: string;
  tone: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex h-6 min-w-0 items-center gap-1.5 rounded-md px-2 text-xs font-medium",
        tone,
      )}
    >
      <Icon className="h-3.5 w-3.5 shrink-0" />
      <span className="truncate">{label}</span>
    </span>
  );
}

export function ProjectRegisterRow({ project }: { project: Project }) {
  const ownerName = project.owner?.full_name || "Владелец не указан";
  const sourceIdeaLabel = project.source_idea?.title || "Без исходной идеи";

  return (
    <Link
      href={`/projects/${project.id}`}
      className="group block rounded-lg border border-border/60 bg-card px-3 py-2.5 shadow-sm transition-colors hover:border-primary/25 hover:bg-muted/20 sm:px-4"
    >
      <div className="flex min-w-0 flex-col gap-2">
        <div className="flex min-w-0 items-start justify-between gap-3">
          <div className="min-w-0 space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <ProjectStatusBadge status={project.status} />
              <span className="inline-flex min-w-0 items-center gap-1.5 text-xs text-muted-foreground">
                <CalendarClock className="h-3.5 w-3.5 shrink-0" />
                <span className="truncate">
                  Создан {formatDate(project.created_at)} · обновлён{" "}
                  {formatDate(project.updated_at)}
                </span>
              </span>
            </div>
            <h2 className="line-clamp-2 break-words text-sm font-semibold leading-5 text-foreground group-hover:text-primary">
              {project.title}
            </h2>
          </div>

          <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors group-hover:bg-primary/10 group-hover:text-primary">
            <ArrowRight className="h-4 w-4" />
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-1.5 border-t border-border/50 pt-2">
          <MetaPill
            label="Владелец"
            value={ownerName}
            avatarName={ownerName}
            avatarUrl={project.owner?.avatar_url}
          />
          <MetaPill
            icon={Lightbulb}
            label="Источник"
            value={sourceIdeaLabel}
          />
          <ProgressMetric
            icon={Building2}
            label={formatProjectDepartmentProgress(project)}
            tone="bg-status-done-bg/55 text-status-done-fg"
          />
          <ProgressMetric
            icon={Flag}
            label={formatProjectMilestoneProgress(project)}
            tone="bg-status-progress-bg/65 text-status-progress-fg"
          />
          <ProgressMetric
            icon={ListChecks}
            label={formatProjectTaskProgress(project)}
            tone="bg-muted text-muted-foreground"
          />
        </div>
      </div>
    </Link>
  );
}
