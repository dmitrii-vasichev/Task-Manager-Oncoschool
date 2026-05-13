"use client";

import Link from "next/link";
import { ArrowRight, CheckCircle2, ListChecks } from "lucide-react";
import { IdeaStatusBadge } from "@/components/ideas/IdeaStatusBadge";
import { UserAvatar } from "@/components/shared/UserAvatar";
import {
  formatIdeaDepartmentProgress,
  formatIdeaTaskProgress,
} from "@/lib/ideaUtils";
import { parseUTCDate } from "@/lib/dateUtils";
import { cn } from "@/lib/utils";
import type { Idea } from "@/lib/types";

function formatUpdatedAt(value: string): string {
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

function ProgressMetric({
  icon: Icon,
  label,
  tone,
}: {
  icon: typeof CheckCircle2;
  label: string;
  tone: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex min-w-0 items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium",
        tone,
      )}
    >
      <Icon className="h-3.5 w-3.5 shrink-0" />
      <span className="truncate">{label}</span>
    </span>
  );
}

export function IdeaRegisterRow({ idea }: { idea: Idea }) {
  const authorName = idea.author?.full_name || "Автор не указан";
  const reviewOwnerName = idea.review_owner?.full_name || "Ответственный не указан";

  return (
    <Link
      href={`/ideas/${idea.id}`}
      className="group block rounded-lg border border-border/60 bg-card px-3 py-3 shadow-sm transition-colors hover:border-primary/25 hover:bg-muted/20 sm:px-4"
    >
      <div className="grid gap-3 lg:grid-cols-[minmax(0,1.35fr)_minmax(260px,0.85fr)_auto] lg:items-center">
        <div className="min-w-0 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <IdeaStatusBadge status={idea.status} />
            <span className="text-xs text-muted-foreground">
              Обновлено {formatUpdatedAt(idea.updated_at)}
            </span>
          </div>
          <h2 className="line-clamp-2 break-words text-sm font-semibold leading-5 text-foreground group-hover:text-primary">
            {idea.title}
          </h2>
        </div>

        <div className="grid min-w-0 gap-2 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
          <PersonSummary
            label="Автор"
            name={authorName}
            avatarUrl={idea.author?.avatar_url}
          />
          <PersonSummary
            label="Ревью"
            name={reviewOwnerName}
            avatarUrl={idea.review_owner?.avatar_url}
          />
        </div>

        <div className="flex min-w-0 flex-col gap-2 sm:flex-row sm:items-center lg:flex-col lg:items-end xl:flex-row">
          <ProgressMetric
            icon={CheckCircle2}
            label={formatIdeaDepartmentProgress(idea)}
            tone="bg-status-done-bg/55 text-status-done-fg"
          />
          <ProgressMetric
            icon={ListChecks}
            label={formatIdeaTaskProgress(idea)}
            tone="bg-muted text-muted-foreground"
          />
          <span className="hidden h-8 w-8 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors group-hover:bg-primary/10 group-hover:text-primary lg:inline-flex">
            <ArrowRight className="h-4 w-4" />
          </span>
        </div>
      </div>
    </Link>
  );
}
