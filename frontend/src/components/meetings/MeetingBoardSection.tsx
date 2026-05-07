"use client";

import { AlertTriangle } from "lucide-react";
import { TaskCard } from "@/components/tasks/TaskCard";
import { cn } from "@/lib/utils";
import type { MeetingBoardSectionKey, Task } from "@/lib/types";
import {
  getMeetingBoardSectionMeta,
  isMeetingBoardTaskOverdue,
} from "./meetingBoardUtils";

interface MeetingBoardSectionProps {
  sectionKey: MeetingBoardSectionKey;
  tasks: Task[];
}

export function MeetingBoardSection({
  sectionKey,
  tasks,
}: MeetingBoardSectionProps) {
  const meta = getMeetingBoardSectionMeta(sectionKey);
  const overdueCount = tasks.filter((task) => isMeetingBoardTaskOverdue(task)).length;

  return (
    <section className={cn("rounded-xl border p-3", meta.tone)}>
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="min-w-0">
          <h2 className="truncate text-sm font-heading font-semibold text-foreground">
            {meta.label}
          </h2>
          {overdueCount > 0 && (
            <p className="mt-0.5 inline-flex items-center gap-1 text-2xs font-medium text-destructive">
              <AlertTriangle className="h-3 w-3" />
              Просрочено: {overdueCount}
            </p>
          )}
        </div>

        <span className="shrink-0 rounded-full bg-background/80 px-2 py-0.5 text-2xs font-semibold text-muted-foreground ring-1 ring-inset ring-border/60">
          {tasks.length}
        </span>
      </div>

      {tasks.length > 0 ? (
        <div className="grid gap-3">
          {tasks.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      ) : (
        <div className="flex min-h-28 items-center justify-center rounded-lg border border-dashed border-border/70 bg-background/45 px-3 text-center text-xs text-muted-foreground">
          Задач нет
        </div>
      )}
    </section>
  );
}
