"use client";

import { AlertTriangle, CheckCircle2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { getContentFactoryGuestAttention } from "@/lib/contentFactoryUtils";
import type { CFGuestStory } from "@/lib/types";

type ContentFactoryGuestAttentionPanelProps = {
  story: CFGuestStory;
};

function formatDateTime(value: string | null | undefined): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function ContentFactoryGuestAttentionPanel({
  story,
}: ContentFactoryGuestAttentionPanelProps) {
  const attention = getContentFactoryGuestAttention(story);
  const dueLabel = formatDateTime(attention.dueAt);

  return (
    <section
      className={
        attention.needsAttention
          ? "rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-4 shadow-sm"
          : "rounded-lg border border-border/70 bg-card px-4 py-4 shadow-sm"
      }
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h2 className="inline-flex items-center gap-2 text-sm font-semibold text-foreground">
            {attention.needsAttention ? (
              <AlertTriangle className="h-4 w-4 text-red-600" />
            ) : (
              <CheckCircle2 className="h-4 w-4 text-status-done-fg" />
            )}
            Следующее действие
          </h2>
          <p className="mt-2 text-sm leading-6 text-foreground">
            {attention.nextAction}
          </p>
          {dueLabel && (
            <p className="mt-1 text-xs text-muted-foreground">
              Срок: {dueLabel}
            </p>
          )}
        </div>
        <Badge
          variant="outline"
          className={
            attention.needsAttention
              ? "border-red-500/25 bg-red-500/10 text-red-700"
              : "border-status-done-fg/30 bg-status-done-bg text-status-done-fg"
          }
        >
          {attention.needsAttention
            ? "Требует внимания"
            : "Сейчас без срочных действий"}
        </Badge>
      </div>

      {attention.needsAttention && (
        <div className="mt-3 flex flex-wrap gap-2">
          {attention.reasons.map((reason) => (
            <Badge
              key={reason.key}
              className="border-red-500/25 bg-red-500/10 text-red-700"
            >
              {reason.label}
            </Badge>
          ))}
        </div>
      )}
    </section>
  );
}
