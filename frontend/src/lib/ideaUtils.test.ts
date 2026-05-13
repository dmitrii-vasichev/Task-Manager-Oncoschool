import assert from "node:assert/strict";
import test from "node:test";

import {
  IDEA_STATUS_LABELS,
  canCompleteIdea,
  countReadyIdeaDepartments,
  formatIdeaDepartmentProgress,
  formatIdeaTaskProgress,
} from "./ideaUtils.ts";
import type { Idea } from "./types.ts";

test("idea labels expose Russian status names used by the Ideas UI", () => {
  assert.equal(IDEA_STATUS_LABELS.in_tasks, "В задачах");
  assert.equal(IDEA_STATUS_LABELS.completed, "Завершена");
});

test("countReadyIdeaDepartments counts ready and not required departments", () => {
  assert.equal(
    countReadyIdeaDepartments([
      { status: "ready" },
      { status: "not_required" },
      { status: "in_progress" },
    ]),
    2,
  );
});

test("canCompleteIdea returns the backend completion flag", () => {
  assert.equal(canCompleteIdea({ can_complete: true }), true);
  assert.equal(canCompleteIdea({ can_complete: false }), false);
});

test("idea progress formatters show ready departments and closed tasks", () => {
  const idea = {
    departments: [{ status: "ready" }, { status: "in_progress" }],
    linked_task_count: 3,
    completed_linked_task_count: 1,
    task_links: [],
  } as unknown as Pick<
    Idea,
    | "completed_linked_task_count"
    | "departments"
    | "linked_task_count"
    | "task_links"
  >;

  assert.equal(formatIdeaDepartmentProgress(idea), "1/2 отделов готово");
  assert.equal(formatIdeaTaskProgress(idea), "1/3 задач закрыто");
});
