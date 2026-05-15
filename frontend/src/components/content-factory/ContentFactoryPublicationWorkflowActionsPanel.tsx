"use client";

import { useMemo, useState } from "react";
import { ArrowRight, Loader2, PlayCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/shared/Toast";
import { ContentFactoryStatusBadge } from "@/components/content-factory/ContentFactoryStatusBadge";
import { api } from "@/lib/api";
import {
  getContentFactoryPublicationWorkflowActions,
  type ContentFactoryPublicationWorkflowAction,
} from "@/lib/contentFactoryUtils";
import type { CFPublication } from "@/lib/types";

const SCHEDULE_DISABLED_REASON = "Сначала укажите плановую дату";

function actionButtonClassName(
  tone: ContentFactoryPublicationWorkflowAction["tone"],
): string {
  switch (tone) {
    case "warning":
      return "border-amber-300 bg-amber-50 text-amber-900 hover:bg-amber-100";
    case "muted":
      return "border-border/70 bg-muted/20 text-muted-foreground hover:bg-muted/30";
    default:
      return "";
  }
}

function actionButtonVariant(
  tone: ContentFactoryPublicationWorkflowAction["tone"],
): "default" | "outline" | "destructive" | "secondary" {
  switch (tone) {
    case "primary":
      return "default";
    case "danger":
      return "destructive";
    case "muted":
      return "secondary";
    case "warning":
    case "default":
    default:
      return "outline";
  }
}

export function ContentFactoryPublicationWorkflowActionsPanel({
  publication,
  onSaved,
}: {
  publication: CFPublication;
  onSaved: () => void | Promise<void>;
}) {
  const { toastSuccess, toastError } = useToast();
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const actions = useMemo(
    () => getContentFactoryPublicationWorkflowActions(publication),
    [publication],
  );
  const saving = savingKey !== null;

  async function handleAction(action: ContentFactoryPublicationWorkflowAction) {
    if (action.disabled || saving) return;

    setSavingKey(action.key);
    try {
      await api.updateCFPublication(publication.id, {
        status: action.targetStatus,
      });
      toastSuccess("Статус публикации обновлён");
      await onSaved();
    } catch (err) {
      toastError(
        err instanceof Error
          ? err.message
          : "Не удалось обновить статус публикации",
      );
    } finally {
      setSavingKey(null);
    }
  }

  return (
    <section className="rounded-lg border border-border/70 bg-card px-4 py-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-2">
          <PlayCircle className="mt-0.5 h-4 w-4 text-muted-foreground" />
          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-foreground">
              Быстрые действия
            </h2>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">
              Переводят публикацию на следующий этап без открытия большой формы.
            </p>
          </div>
        </div>
        <ContentFactoryStatusBadge kind="publication" status={publication.status} />
      </div>

      {actions.length === 0 ? (
        <p className="mt-3 rounded-md border border-border/70 bg-muted/20 px-3 py-2 text-xs leading-5 text-muted-foreground">
          Для этого статуса быстрых действий нет. Факт выхода и метрики ведутся ниже.
        </p>
      ) : (
        <div className="mt-3 space-y-2">
          {actions.map((action) => (
            <div
              key={action.key}
              className="rounded-md border border-border/70 bg-muted/10 px-2 py-2"
            >
              <Button
                type="button"
                size="sm"
                variant={actionButtonVariant(action.tone)}
                className={`h-auto min-h-8 w-full justify-between gap-2 whitespace-normal px-2 py-1.5 text-left ${actionButtonClassName(
                  action.tone,
                )}`}
                disabled={saving || action.disabled}
                onClick={() => void handleAction(action)}
              >
                <span className="min-w-0">{action.label}</span>
                {savingKey === action.key ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <ArrowRight className="h-3.5 w-3.5" />
                )}
              </Button>
              <div className="mt-1.5 flex flex-wrap items-center gap-2 px-1 text-xs leading-5 text-muted-foreground">
                <span>{action.description}</span>
                {action.disabledReason ? (
                  <span className="font-medium text-amber-800">
                    {action.disabledReason || SCHEDULE_DISABLED_REASON}
                  </span>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
