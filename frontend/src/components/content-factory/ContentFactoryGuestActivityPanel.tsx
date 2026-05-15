"use client";

import { useMemo, useState, type FormEvent } from "react";
import { History, Loader2, MessageSquare, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/shared/Toast";
import { api } from "@/lib/api";
import { getContentFactoryDisplayName } from "@/lib/contentFactoryUtils";
import type { CFGuestStoryEvent, TeamMember } from "@/lib/types";

type ContentFactoryGuestActivityPanelProps = {
  guestStoryId: string;
  events: CFGuestStoryEvent[];
  members: TeamMember[];
  onEventCreated: () => void | Promise<void>;
};

const EVENT_LABELS: Record<CFGuestStoryEvent["event_type"], string> = {
  created: "История создана",
  comment: "Комментарий",
  status_changed: "Статус изменён",
  consent_changed: "Согласие изменено",
  gift_changed: "Подарок изменён",
  follow_up_changed: "Follow-up изменён",
};

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Без даты";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function eventActorName(event: CFGuestStoryEvent, members: TeamMember[]): string {
  return event.actor_id
    ? getContentFactoryDisplayName(event.actor_id, members)
    : "Система";
}

export function ContentFactoryGuestActivityPanel({
  guestStoryId,
  events,
  members,
  onEventCreated,
}: ContentFactoryGuestActivityPanelProps) {
  const { toastSuccess, toastError } = useToast();
  const [body, setBody] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sortedEvents = useMemo(
    () =>
      [...events].sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      ),
    [events],
  );

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const cleanBody = body.trim();
    if (!cleanBody) {
      setError("Напишите комментарий");
      return;
    }

    setSaving(true);
    setError(null);
    try {
      await api.createCFGuestStoryEvent(guestStoryId, { body: cleanBody });
      setBody("");
      toastSuccess("Комментарий добавлен");
      await onEventCreated();
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Не удалось добавить комментарий";
      setError(message);
      toastError(message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="rounded-lg border border-border/70 bg-card px-4 py-4 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="inline-flex items-center gap-2 text-sm font-semibold text-foreground">
            <History className="h-4 w-4 text-primary" />
            Журнал истории
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Комментарии команды и важные изменения по гостю.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="mt-4 space-y-2">
        <Textarea
          value={body}
          onChange={(event) => setBody(event.target.value)}
          className="min-h-20 border-border/70 bg-muted/20 text-sm"
          placeholder="Добавьте комментарий: договорённость, риск, уточнение по согласию..."
          disabled={saving}
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <div className="flex justify-end">
          <Button
            type="submit"
            size="sm"
            className="h-8 gap-1.5 rounded-md px-3 text-xs"
            disabled={saving}
          >
            {saving ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Send className="h-3.5 w-3.5" />
            )}
            Добавить
          </Button>
        </div>
      </form>

      <div className="mt-4 space-y-2">
        {sortedEvents.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border/70 bg-muted/20 px-4 py-8 text-center">
            <MessageSquare className="mx-auto h-7 w-7 text-muted-foreground" />
            <p className="mt-2 text-sm font-medium text-foreground">
              Событий пока нет
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              Первый комментарий появится здесь.
            </p>
          </div>
        ) : (
          sortedEvents.map((event) => (
            <article
              key={event.id}
              className="rounded-lg border border-border/60 bg-muted/20 px-3 py-3"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-sm font-semibold text-foreground">
                  {EVENT_LABELS[event.event_type]}
                </span>
                <span className="text-xs text-muted-foreground">
                  {formatDateTime(event.created_at)}
                </span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {eventActorName(event, members)}
              </p>
              {event.body && (
                <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-foreground">
                  {event.body}
                </p>
              )}
              {(event.old_value || event.new_value) && (
                <p className="mt-2 text-sm text-muted-foreground">
                  Было: {event.old_value || "не указано"} · Стало:{" "}
                  {event.new_value || "не указано"}
                </p>
              )}
            </article>
          ))
        )}
      </div>
    </section>
  );
}
