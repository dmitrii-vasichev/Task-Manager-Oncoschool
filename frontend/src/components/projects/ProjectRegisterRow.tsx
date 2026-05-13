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

function PersonSummary({
  label,
  name,
  avatarUrl,
}: {
  label: string;
  name: string;
  avatarUrl?: string | null;
}) {
  return (
    <div className="flex min-w-0 items-center gap-2">
      <UserAvatar name={name} avatarUrl={avatarUrl || null} size="sm" />
      <div className="min-w-0">
        <p className="text-2xs font-medium uppercase text-muted-foreground">
          {label}
        </p>
        <p className="truncate text-xs text-foreground">{name}</p>
      </div>
    </div>
  );
}

function TextSummary({
  icon: Icon,
  label,
  value,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
}) {
  return (
    <div className="flex min-w-0 items-center gap-2">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground">
        <Icon className="h-3.5 w-3.5" />
      </span>
      <div className="min-w-0">
        <p className="text-2xs font-medium uppercase text-muted-foreground">
          {label}
        </p>
        <p className="truncate text-xs text-foreground">{value}</p>
      </div>
    </div>
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
        "inline-flex h-7 min-w-0 items-center gap-1.5 rounded-md px-2 text-xs font-medium",
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
      className="group block rounded-lg border border-border/60 bg-card px-3 py-3 shadow-sm transition-colors hover:border-primary/25 hover:bg-muted/20 sm:px-4"
    >
      <div className="grid gap-3 xl:grid-cols-[minmax(0,1.1fr)_minmax(280px,0.9fr)_auto] xl:items-center">
        <div className="min-w-0 space-y-2">
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

        <div className="grid min-w-0 gap-2 sm:grid-cols-2">
          <PersonSummary
            label="Владелец"
            name={ownerName}
            avatarUrl={project.owner?.avatar_url}
          />
          <TextSummary
            icon={Lightbulb}
            label="Источник"
            value={sourceIdeaLabel}
          />
        </div>

        <div className="flex min-w-0 flex-col gap-2 sm:flex-row sm:items-center xl:flex-col xl:items-end 2xl:flex-row">
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
          <span className="hidden h-8 w-8 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors group-hover:bg-primary/10 group-hover:text-primary xl:inline-flex">
            <ArrowRight className="h-4 w-4" />
          </span>
        </div>
      </div>
    </Link>
  );
}
