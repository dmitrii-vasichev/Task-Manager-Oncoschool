"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import {
  Loader2,
  Plus,
  Pencil,
  Trash2,
  Send,
  MessageCircle,
  Info,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useToast } from "@/components/shared/Toast";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { api } from "@/lib/api";
import type { TelegramNotificationTarget } from "@/lib/types";

const TARGET_TYPE_LABELS: Record<string, string> = {
  meeting: "Встречи",
  "report:getcourse": "Отчёты",
};

type FilterType = "all" | "meeting" | "report:getcourse";

export function TelegramTargetsSection() {
  const { toastSuccess, toastError } = useToast();
  const [targets, setTargets] = useState<TelegramNotificationTarget[]>([]);
  const [loading, setLoading] = useState(true);
  const [editTarget, setEditTarget] = useState<TelegramNotificationTarget | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [filter, setFilter] = useState<FilterType>("all");
  const [deleteTarget, setDeleteTarget] = useState<TelegramNotificationTarget | null>(null);

  const fetchTargets = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getTelegramTargets();
      setTargets(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTargets();
  }, [fetchTargets]);

  const filteredTargets = useMemo(() => {
    if (filter === "all") return targets;
    return targets.filter((t) => t.types.includes(filter));
  }, [targets, filter]);

  const handleDelete = async (target: TelegramNotificationTarget) => {
    try {
      await api.deleteTelegramTarget(target.id);
      toastSuccess("Группа удалена");
      fetchTargets();
    } catch (e) {
      toastError(e instanceof Error ? e.message : "Ошибка удаления");
    } finally {
      setDeleteTarget(null);
    }
  };

  if (loading) {
    return (
      <div className="rounded-2xl border border-border/60 bg-card p-6 space-y-4">
        <Skeleton className="h-6 w-48" />
        <div className="space-y-2">
          {[...Array(2)].map((_, i) => (
            <Skeleton key={i} className="h-16 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="rounded-2xl border border-border/60 bg-card overflow-hidden">
        {/* Section header */}
        <div className="flex items-center gap-3 p-6 pb-0">
          <div
            className="h-9 w-9 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: "hsl(200, 60%, 50%, 0.1)" }}
          >
            <Send
              className="h-5 w-5"
              style={{ color: "hsl(200, 60%, 50%)" }}
            />
          </div>
          <div className="flex-1">
            <h2 className="font-heading font-semibold text-base">
              Telegram-группы для уведомлений
            </h2>
            <p className="text-xs text-muted-foreground">
              Группы для отправки уведомлений и (опционально) входящих задач через @бот
            </p>
          </div>
          <Button
            size="sm"
            className="rounded-lg gap-1.5"
            onClick={() => {
              setEditTarget(null);
              setShowForm(true);
            }}
          >
            <Plus className="h-3.5 w-3.5" />
            Добавить
          </Button>
        </div>

        {/* Filter chips */}
        <div className="px-6 pt-4 flex gap-1.5 flex-wrap">
          {(["all", "meeting", "report:getcourse"] as FilterType[]).map((f) => {
            const isActive = filter === f;
            const count =
              f === "all"
                ? targets.length
                : targets.filter((t) => t.types.includes(f)).length;
            const label =
              f === "all" ? "Все" : TARGET_TYPE_LABELS[f] ?? f;
            return (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
              >
                {label}
                <span
                  className={`inline-flex items-center justify-center rounded-full min-w-[18px] h-[18px] px-1 text-2xs font-semibold ${
                    isActive
                      ? "bg-primary-foreground/20 text-primary-foreground"
                      : "bg-background/60 text-muted-foreground"
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        <div className="p-6 space-y-3">
          {filteredTargets.length === 0 ? (
            <div className="rounded-xl border border-dashed border-border/60 bg-muted/20 p-6 text-center">
              <MessageCircle className="h-7 w-7 text-muted-foreground/40 mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">Нет настроенных групп</p>
              <p className="text-xs text-muted-foreground/60 mt-1">
                Добавьте Telegram-группы для уведомлений
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {filteredTargets.map((target) => (
                <div
                  key={target.id}
                  className="group flex items-center gap-3 p-3.5 rounded-xl border border-border/60 hover:shadow-sm hover:border-border"
                >
                  <div
                    className="h-9 w-9 rounded-lg flex items-center justify-center shrink-0"
                    style={{ backgroundColor: "hsl(200, 60%, 50%, 0.08)" }}
                  >
                    <Send className="h-4 w-4" style={{ color: "hsl(200, 60%, 50%)" }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-heading font-semibold truncate">
                        {target.label || `Chat ${target.chat_id}`}
                      </p>
                      {/* Type badges */}
                      <div className="flex gap-1 shrink-0">
                        {target.types.map((t) => (
                          <span
                            key={t}
                            className="inline-flex items-center rounded-full px-1.5 py-0.5 text-2xs font-medium bg-muted text-muted-foreground"
                          >
                            {TARGET_TYPE_LABELS[t] ?? t}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-2xs text-muted-foreground">
                      <span>ID: {target.chat_id}</span>
                      {target.thread_id && (
                        <>
                          <span className="text-border">|</span>
                          <span>Тема: #{target.thread_id}</span>
                        </>
                      )}
                      {target.allow_incoming_tasks && (
                        <>
                          <span className="text-border">|</span>
                          <span>Входящие задачи: вкл</span>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Status dot */}
                  <div
                    className={`h-2 w-2 rounded-full shrink-0 ${
                      target.is_active ? "bg-status-done-fg" : "bg-border"
                    }`}
                  />

                  {/* Actions */}
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 rounded-lg text-muted-foreground hover:text-foreground"
                      onClick={() => {
                        setEditTarget(target);
                        setShowForm(true);
                      }}
                    >
                      <Pencil className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 rounded-lg text-muted-foreground hover:text-destructive"
                      onClick={() => setDeleteTarget(target)}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Help text */}
          <div className="flex items-start gap-2.5 text-xs text-muted-foreground bg-muted/40 p-3.5 rounded-xl border border-border/40">
            <Info className="h-4 w-4 mt-0.5 shrink-0 text-primary/60" />
            <span>
              Чтобы узнать Chat ID группы, добавьте бота @userinfobot в группу
              или перешлите сообщение из группы боту @JsonDumpBot.
              Включайте «Входящие задачи», только если в этой группе хотите создавать задачи через @бот.
            </span>
          </div>
        </div>
      </div>

      {/* Telegram target form dialog */}
      {showForm && (
        <TelegramTargetFormDialog
          target={editTarget}
          onClose={() => {
            setShowForm(false);
            setEditTarget(null);
          }}
          onSaved={() => {
            fetchTargets();
            setShowForm(false);
            setEditTarget(null);
          }}
        />
      )}

      {/* Delete confirmation */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title={`Удалить «${deleteTarget?.label || `Chat ${deleteTarget?.chat_id}`}»?`}
        description="Telegram-группа будет удалена из списка целей для уведомлений."
        onConfirm={() => deleteTarget && handleDelete(deleteTarget)}
      />
    </>
  );
}

// ============================================
// Telegram Target Form Dialog
// ============================================

const AVAILABLE_TYPES = [
  { value: "meeting", label: "Встречи", description: "Напоминания и уведомления о встречах" },
  { value: "report:getcourse", label: "Отчёты", description: "Ежедневные отчёты GetCourse" },
];

function TelegramTargetFormDialog({
  target,
  onClose,
  onSaved,
}: {
  target: TelegramNotificationTarget | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { toastSuccess, toastError } = useToast();
  const isEdit = !!target;
  const [chatId, setChatId] = useState(target ? String(target.chat_id) : "");
  const [threadId, setThreadId] = useState(
    target?.thread_id ? String(target.thread_id) : ""
  );
  const [label, setLabel] = useState(target?.label ?? "");
  const [selectedTypes, setSelectedTypes] = useState<string[]>(
    target?.types?.length ? target.types : ["meeting"]
  );
  const [allowIncomingTasks, setAllowIncomingTasks] = useState(
    target?.allow_incoming_tasks ?? false
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleType = (typeValue: string) => {
    setSelectedTypes((prev) =>
      prev.includes(typeValue)
        ? prev.filter((t) => t !== typeValue)
        : [...prev, typeValue]
    );
  };

  const handleSave = async () => {
    const chatIdNum = Number(chatId);
    if (!chatId || isNaN(chatIdNum)) {
      setError("Введите корректный Chat ID");
      return;
    }
    if (selectedTypes.length === 0) {
      setError("Выберите хотя бы одну категорию уведомлений");
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const data = {
        chat_id: chatIdNum,
        thread_id: threadId ? Number(threadId) : null,
        label: label.trim() || null,
        types: selectedTypes,
        allow_incoming_tasks: allowIncomingTasks,
      };

      if (isEdit && target) {
        await api.updateTelegramTarget(target.id, data);
        toastSuccess("Группа обновлена");
      } else {
        await api.createTelegramTarget(data);
        toastSuccess("Группа добавлена");
      }
      onSaved();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Ошибка сохранения";
      setError(msg);
      toastError(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="font-heading">
            {isEdit ? "Редактировать группу" : "Добавить Telegram-группу"}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 pt-2">
          <div>
            <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Название (для удобства)
            </Label>
            <Input
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="Основная группа"
              className="mt-1.5 rounded-xl"
            />
          </div>

          <div>
            <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Chat ID *
            </Label>
            <Input
              value={chatId}
              onChange={(e) => setChatId(e.target.value)}
              placeholder="-1003693766132"
              className="mt-1.5 rounded-xl font-mono text-sm"
            />
          </div>

          <div>
            <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Thread ID (необязательно)
            </Label>
            <Input
              value={threadId}
              onChange={(e) => setThreadId(e.target.value)}
              placeholder="Оставьте пустым для общей ветки"
              className="mt-1.5 rounded-xl font-mono text-sm"
            />
            <p className="text-2xs text-muted-foreground mt-1">
              Укажите, если группа использует темы (topics)
            </p>
          </div>

          {/* Type checkboxes */}
          <div>
            <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Категории уведомлений *
            </Label>
            <div className="mt-1.5 space-y-2">
              {AVAILABLE_TYPES.map((t) => {
                const isChecked = selectedTypes.includes(t.value);
                return (
                  <button
                    key={t.value}
                    type="button"
                    onClick={() => toggleType(t.value)}
                    className={`w-full flex items-center gap-3 p-3 rounded-xl border transition-colors text-left ${
                      isChecked
                        ? "border-primary/40 bg-primary/5"
                        : "border-border/60 bg-muted/20 hover:border-border"
                    }`}
                  >
                    <div
                      className={`h-4 w-4 rounded border-2 flex items-center justify-center shrink-0 transition-colors ${
                        isChecked
                          ? "border-primary bg-primary"
                          : "border-muted-foreground/40"
                      }`}
                    >
                      {isChecked && (
                        <CheckCircle2 className="h-3 w-3 text-primary-foreground" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium">{t.label}</p>
                      <p className="text-2xs text-muted-foreground">{t.description}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="rounded-xl border border-border/60 bg-muted/20 p-3.5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <Label className="text-sm font-medium">Входящие задачи через @бот</Label>
                <p className="text-2xs text-muted-foreground mt-1">
                  Если включено, в этой группе можно ставить задачи с упоминанием бота.
                </p>
              </div>
              <Switch
                checked={allowIncomingTasks}
                onCheckedChange={setAllowIncomingTasks}
                disabled={saving}
              />
            </div>
          </div>

          {error && (
            <div className="rounded-xl bg-destructive/10 border border-destructive/20 p-3">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}

          <div className="flex gap-2 justify-end pt-2">
            <Button
              variant="outline"
              className="rounded-xl"
              onClick={onClose}
              disabled={saving}
            >
              Отмена
            </Button>
            <Button className="rounded-xl" onClick={handleSave} disabled={saving}>
              {saving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Сохранение...
                </>
              ) : isEdit ? (
                "Сохранить"
              ) : (
                "Добавить"
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
