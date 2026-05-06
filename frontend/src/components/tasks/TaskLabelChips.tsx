"use client";

import type { TaskLabel } from "@/lib/types";
import { cn } from "@/lib/utils";

const LABEL_CLASSES: Record<string, string> = {
  teal: "bg-primary/10 text-primary border-primary/20",
  coral: "bg-accent/10 text-accent-foreground border-accent/30",
  blue: "bg-blue-500/10 text-blue-700 border-blue-500/20 dark:text-blue-300",
  purple: "bg-purple-500/10 text-purple-700 border-purple-500/20 dark:text-purple-300",
  gold: "bg-amber-500/10 text-amber-700 border-amber-500/20 dark:text-amber-300",
  green: "bg-emerald-500/10 text-emerald-700 border-emerald-500/20 dark:text-emerald-300",
  slate: "bg-slate-500/10 text-slate-700 border-slate-500/20 dark:text-slate-300",
};

function labelClass(color: string) {
  return LABEL_CLASSES[color] || LABEL_CLASSES.slate;
}

export function TaskLabelChips({
  labels,
  maxVisible = 2,
  className,
}: {
  labels: TaskLabel[];
  maxVisible?: number;
  className?: string;
}) {
  if (!labels.length) return null;

  const visible = labels.slice(0, maxVisible);
  const hiddenCount = labels.length - visible.length;

  return (
    <div className={cn("flex min-w-0 flex-wrap gap-1.5", className)}>
      {visible.map((label) => (
        <span
          key={label.id}
          className={cn(
            "inline-flex max-w-full items-center rounded-full border px-2 py-0.5 text-2xs font-medium leading-4",
            labelClass(label.color)
          )}
          title={label.name}
        >
          <span className="truncate">{label.name}</span>
        </span>
      ))}
      {hiddenCount > 0 && (
        <span className="inline-flex items-center rounded-full border border-border/60 bg-muted px-2 py-0.5 text-2xs font-medium text-muted-foreground">
          +{hiddenCount}
        </span>
      )}
    </div>
  );
}
