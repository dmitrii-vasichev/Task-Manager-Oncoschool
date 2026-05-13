import assert from "node:assert/strict";
import test from "node:test";

import { formatIdeaEvent } from "./ideaEventUtils.ts";
import type { IdeaEvent } from "./types.ts";

function event(event_type: string, payload: Record<string, unknown>): IdeaEvent {
  return {
    id: "event-1",
    idea_id: "idea-1",
    actor_id: "member-1",
    event_type,
    payload,
    created_at: "2026-05-13T07:13:00",
    actor: null,
  };
}

test("formatIdeaEvent renders status changes with Russian status labels", () => {
  const formatted = formatIdeaEvent(
    event("status_changed", {
      old_status: "new",
      new_status: "accepted",
    }),
  );

  assert.equal(formatted.title, "Статус изменён");
  assert.equal(formatted.detail, "Новая → Принята");
});

test("formatIdeaEvent renders known idea events without raw event types", () => {
  assert.equal(formatIdeaEvent(event("idea_created", {})).title, "Идея создана");
  assert.equal(
    formatIdeaEvent(event("decision_recorded", { status: "rejected", comment: "Дубль" })).detail,
    "Отклонена · Дубль",
  );
});

test("formatIdeaEvent falls back to a readable generic label", () => {
  const formatted = formatIdeaEvent(event("unexpected_raw_event", {}));

  assert.equal(formatted.title, "Обновление идеи");
  assert.equal(formatted.detail, null);
});
