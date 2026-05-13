import assert from "node:assert/strict";
import test from "node:test";

import { formatProjectEvent } from "./projectEventUtils.ts";
import type { ProjectEvent } from "./types.ts";

function event(event_type: string, payload: Record<string, unknown>): ProjectEvent {
  return {
    id: "event-1",
    project_id: "project-1",
    actor_id: "member-1",
    event_type,
    payload,
    created_at: "2026-05-13T07:13:00",
    actor: null,
  };
}

test("formatProjectEvent renders status changes with Russian status labels", () => {
  const formatted = formatProjectEvent(
    event("status_changed", {
      old_status: "planned",
      new_status: "in_progress",
    }),
  );

  assert.equal(formatted.title, "Статус изменён");
  assert.equal(formatted.detail, "Запланирован → В работе");
});

test("formatProjectEvent avoids raw event keys", () => {
  const cases = [
    ["project_created", "Проект создан"],
    ["project_updated", "Проект обновлён"],
    ["status_changed", "Статус изменён"],
    ["department_added", "Добавлен отдел"],
    ["department_updated", "Отдел обновлён"],
    ["milestone_added", "Добавлен этап"],
    ["milestone_updated", "Этап обновлён"],
    ["task_linked", "Создана задача по проекту"],
    ["comment_added", "Добавлен комментарий"],
    ["project_completed", "Проект завершён"],
    ["project_deleted", "Проект удалён"],
  ] as const;

  for (const [eventType, title] of cases) {
    assert.equal(formatProjectEvent(event(eventType, {})).title, title);
  }
});

test("formatProjectEvent renders project update fields and milestone dates", () => {
  assert.equal(
    formatProjectEvent(event("project_updated", { fields: ["title", "owner_id"] })).detail,
    "Изменено: название, ответственный",
  );
  assert.equal(
    formatProjectEvent(event("milestone_updated", { due_date: "2026-05-13" })).detail,
    "Дата: 13.05.2026",
  );
});
