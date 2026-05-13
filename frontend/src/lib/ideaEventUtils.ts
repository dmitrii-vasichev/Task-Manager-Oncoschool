import {
  IDEA_DEPARTMENT_STATUS_LABELS,
  IDEA_STATUS_LABELS,
} from "./ideaUtils.ts";
import type { IdeaDepartmentStatus, IdeaEvent, IdeaStatus } from "./types.ts";

export interface IdeaEventPresentation {
  title: string;
  detail: string | null;
}

const IDEA_FIELD_LABELS: Record<string, string> = {
  title: "название",
  description: "описание",
  review_owner_id: "ответственный за review",
};

const IDEA_DEPARTMENT_FIELD_LABELS: Record<string, string> = {
  owner_id: "ответственный",
  status: "статус",
  note: "заметка",
};

function isIdeaStatus(value: unknown): value is IdeaStatus {
  return typeof value === "string" && value in IDEA_STATUS_LABELS;
}

function isIdeaDepartmentStatus(value: unknown): value is IdeaDepartmentStatus {
  return typeof value === "string" && value in IDEA_DEPARTMENT_STATUS_LABELS;
}

function statusLabel(value: unknown): string | null {
  if (!isIdeaStatus(value)) return typeof value === "string" ? value : null;
  return IDEA_STATUS_LABELS[value];
}

function departmentStatusLabel(value: unknown): string | null {
  if (!isIdeaDepartmentStatus(value)) {
    return typeof value === "string" ? value : null;
  }
  return IDEA_DEPARTMENT_STATUS_LABELS[value];
}

function payloadString(payload: Record<string, unknown>, key: string): string | null {
  const value = payload[key];
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function formatIsoDate(value: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return value;
  return `${match[3]}.${match[2]}.${match[1]}`;
}

function changedFieldsLabel(
  payload: Record<string, unknown>,
  labels: Record<string, string>,
): string | null {
  const fields = payload.fields;
  if (!Array.isArray(fields)) return null;

  const readableFields = fields
    .filter((field): field is string => typeof field === "string")
    .map((field) => labels[field] || field);

  if (readableFields.length === 0) return null;
  return `Изменено: ${readableFields.join(", ")}`;
}

export function formatIdeaEvent(event: IdeaEvent): IdeaEventPresentation {
  const payload = event.payload || {};

  switch (event.event_type) {
    case "idea_created":
      return {
        title: "Идея создана",
        detail: payloadString(payload, "title"),
      };
    case "idea_updated":
      return {
        title: "Идея обновлена",
        detail: changedFieldsLabel(payload, IDEA_FIELD_LABELS),
      };
    case "status_changed": {
      const oldStatus = statusLabel(payload.old_status);
      const newStatus = statusLabel(payload.new_status);
      return {
        title: "Статус изменён",
        detail: oldStatus && newStatus ? `${oldStatus} → ${newStatus}` : newStatus,
      };
    }
    case "decision_recorded": {
      const status = statusLabel(payload.status);
      const comment = payloadString(payload, "comment");
      const deferredUntil = payloadString(payload, "deferred_until");
      const details = [
        status,
        deferredUntil ? `до ${formatIsoDate(deferredUntil)}` : null,
        comment,
      ].filter(Boolean);

      return {
        title: "Решение зафиксировано",
        detail: details.length > 0 ? details.join(" · ") : null,
      };
    }
    case "department_added":
      return {
        title: "Добавлен отдел",
        detail: null,
      };
    case "department_updated": {
      const status = departmentStatusLabel(payload.status);
      return {
        title: "Отдел обновлён",
        detail: status || changedFieldsLabel(payload, IDEA_DEPARTMENT_FIELD_LABELS),
      };
    }
    case "task_linked":
      return {
        title: "Создана задача по идее",
        detail: null,
      };
    case "comment_added":
      return {
        title: "Добавлен комментарий",
        detail: null,
      };
    case "idea_completed":
      return {
        title: "Идея завершена",
        detail: null,
      };
    case "idea_reopened":
      return {
        title: "Идея возвращена в работу",
        detail: null,
      };
    case "idea_deleted":
      return {
        title: "Идея удалена",
        detail: statusLabel(payload.status),
      };
    default:
      return {
        title: "Обновление идеи",
        detail: null,
      };
  }
}
