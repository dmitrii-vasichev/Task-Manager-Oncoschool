"use client";

import { useState } from "react";
import { Building2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { UserAvatar } from "@/components/shared/UserAvatar";
import { useToast } from "@/components/shared/Toast";
import { IDEA_DEPARTMENT_STATUS_LABELS } from "@/lib/ideaUtils";
import { api } from "@/lib/api";
import type { Idea, IdeaDepartmentStatus } from "@/lib/types";

const DEPARTMENT_ACTION_STATUSES: IdeaDepartmentStatus[] = [
  "in_progress",
  "ready",
  "not_required",
];

export function IdeaDepartmentPanel({
  idea,
  onUpdated,
}: {
  idea: Idea;
  onUpdated: (idea: Idea) => void;
}) {
  const { toastSuccess, toastError } = useToast();
  const [savingByDepartment, setSavingByDepartment] = useState<
    Partial<Record<string, IdeaDepartmentStatus>>
  >({});

  async function handleDepartmentStatusChange(
    ideaDepartmentId: string,
    status: IdeaDepartmentStatus,
  ) {
    setSavingByDepartment((current) => ({
      ...current,
      [ideaDepartmentId]: status,
    }));
    try {
      const updated = await api.updateIdeaDepartment(idea.id, ideaDepartmentId, {
        status,
      });
      onUpdated(updated);
      toastSuccess("Статус отдела обновлён");
    } catch (error) {
      toastError(error instanceof Error ? error.message : "Не удалось обновить отдел");
    } finally {
      setSavingByDepartment((current) => {
        const next = { ...current };
        delete next[ideaDepartmentId];
        return next;
      });
    }
  }

  return (
    <section className="rounded-lg border border-border/60 bg-card shadow-sm">
      <div className="border-b border-border/60 px-4 py-3">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-foreground">Отделы</h2>
            <p className="text-xs text-muted-foreground">
              {idea.ready_department_count}/{idea.required_department_count} готово
            </p>
          </div>
          <Building2 className="h-4 w-4 shrink-0 text-muted-foreground" />
        </div>
      </div>

      <div className="space-y-2 px-4 py-3">
        {idea.departments.length === 0 ? (
          <div className="rounded-md border border-dashed border-border/70 bg-muted/20 px-3 py-4 text-sm text-muted-foreground">
            Отделы не назначены
          </div>
        ) : (
          idea.departments.map((department) => {
            const ownerName = department.owner?.full_name || "Владелец не указан";
            const savingStatus = savingByDepartment[department.id];

            return (
              <div
                key={department.id}
                className="grid gap-2 rounded-md border border-border/60 px-3 py-2 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="truncate text-sm font-medium text-foreground">
                      {department.department?.name || "Отдел не указан"}
                    </p>
                    <span className="rounded-full bg-muted px-2 py-0.5 text-2xs font-medium text-muted-foreground">
                      {IDEA_DEPARTMENT_STATUS_LABELS[department.status]}
                    </span>
                  </div>
                  <div className="mt-2 flex min-w-0 items-center gap-2">
                    <UserAvatar
                      name={ownerName}
                      avatarUrl={department.owner?.avatar_url}
                      size="sm"
                    />
                    <p className="truncate text-xs text-muted-foreground">{ownerName}</p>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2 sm:justify-end">
                  <p className="text-xs font-medium text-muted-foreground">
                    {department.task_links.length} задач
                  </p>
                  <div className="flex flex-wrap gap-1.5 sm:justify-end">
                    {DEPARTMENT_ACTION_STATUSES.map((status) => {
                      const isSaving = savingStatus === status;
                      const isDisabled = Boolean(savingStatus) || department.status === status;

                      return (
                        <Button
                          key={status}
                          type="button"
                          size="sm"
                          variant="outline"
                          disabled={isDisabled}
                          onClick={() => handleDepartmentStatusChange(department.id, status)}
                          className="h-7 rounded-md px-2 text-2xs"
                        >
                          {isSaving && <Loader2 className="h-3 w-3 animate-spin" />}
                          {IDEA_DEPARTMENT_STATUS_LABELS[status]}
                        </Button>
                      );
                    })}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}
