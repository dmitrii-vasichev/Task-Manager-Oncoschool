"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  FileText,
  Loader2,
  Bot,
  CheckCircle2,
  ListChecks,
  Users,
  Trash2,
  Plus,
  Search,
  ArrowLeft,
  Sparkles,
  X,
} from "lucide-react";
import { ModeratorGuard } from "@/components/shared/ModeratorGuard";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { UserAvatar } from "@/components/shared/UserAvatar";
import { useToast } from "@/components/shared/Toast";
import { api } from "@/lib/api";
import type {
  ParseSummaryResponse,
  ParsedTask,
  AISettingsResponse,
  TaskPriority,
} from "@/lib/types";

type Step = "input" | "preview";

const PRIORITY_COLORS: Record<TaskPriority, string> = {
  urgent: "bg-priority-urgent-bg text-priority-urgent-fg border-priority-urgent-fg/20",
  high: "bg-priority-high-bg text-priority-high-fg border-priority-high-fg/20",
  medium: "bg-priority-medium-bg text-priority-medium-fg border-priority-medium-fg/20",
  low: "bg-priority-low-bg text-priority-low-fg border-priority-low-fg/20",
};

const PRIORITY_LABELS: Record<TaskPriority, string> = {
  urgent: "Срочный",
  high: "Высокий",
  medium: "Средний",
  low: "Низкий",
};

export default function SummaryPage() {
  return (
    <ModeratorGuard>
      <SummaryContent />
    </ModeratorGuard>
  );
}

function SummaryContent() {
  const { toastSuccess, toastError } = useToast();
  const router = useRouter();
  const [step, setStep] = useState<Step>("input");
  const [rawSummary, setRawSummary] = useState("");
  const [parsing, setParsing] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiSettings, setAiSettings] = useState<AISettingsResponse | null>(null);

  const [parsed, setParsed] = useState<ParseSummaryResponse | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editSummary, setEditSummary] = useState("");
  const [editDecisions, setEditDecisions] = useState<string[]>([]);
  const [editTasks, setEditTasks] = useState<ParsedTask[]>([]);
  const [editParticipants, setEditParticipants] = useState<string[]>([]);

  useEffect(() => {
    api.getAiSettings().then(setAiSettings).catch(() => {});
  }, []);

  const handleParse = async () => {
    if (!rawSummary.trim()) return;
    setParsing(true);
    setError(null);
    try {
      const result = await api.parseSummary(rawSummary);
      setParsed(result);
      setEditTitle(result.title);
      setEditSummary(result.summary);
      setEditDecisions([...result.decisions]);
      setEditTasks(result.tasks.map((t) => ({ ...t })));
      setEditParticipants([...result.participants]);
      setStep("preview");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка парсинга");
    } finally {
      setParsing(false);
    }
  };

  const handleCreate = async () => {
    setCreating(true);
    setError(null);
    try {
      const result = await api.createMeeting({
        raw_summary: rawSummary,
        title: editTitle,
        parsed_summary: editSummary,
        decisions: editDecisions,
        participants: editParticipants,
        tasks: editTasks,
      });
      toastSuccess(`Встреча создана с ${editTasks.length} задачами`);
      router.push(`/meetings/${result.meeting.id}`);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Ошибка создания встречи";
      setError(msg);
      toastError(msg);
    } finally {
      setCreating(false);
    }
  };

  const updateTask = (index: number, field: keyof ParsedTask, value: string | null) => {
    setEditTasks((prev) =>
      prev.map((t, i) => (i === index ? { ...t, [field]: value } : t))
    );
  };

  const removeTask = (index: number) => {
    setEditTasks((prev) => prev.filter((_, i) => i !== index));
  };

  const addTask = () => {
    setEditTasks((prev) => [
      ...prev,
      { title: "", description: null, assignee_name: null, priority: "medium" as TaskPriority, deadline: null },
    ]);
  };

  const removeDecision = (index: number) => {
    setEditDecisions((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="max-w-3xl animate-in fade-in duration-300">
      {/* ===== INPUT STEP ===== */}
      {step === "input" && (
        <div className="space-y-6 animate-summary-slide-in">
          {/* Header card */}
          <div className="relative overflow-hidden rounded-2xl border border-border/60 bg-card">
            {/* Decorative gradient */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary/3 via-transparent to-accent/3" />

            <div className="relative p-6 space-y-5">
              {/* Title row */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
                    <FileText className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h2 className="text-lg font-heading font-bold text-foreground">
                      Zoom Summary
                    </h2>
                    <p className="text-sm text-muted-foreground">
                      Вставьте текст — AI извлечёт задачи и решения
                    </p>
                  </div>
                </div>
              </div>

              {/* AI provider chip */}
              {aiSettings && (
                <div className="flex items-center gap-2">
                  <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-muted/60 text-sm">
                    <Bot className="h-3.5 w-3.5 text-primary" />
                    <span className="text-muted-foreground">Обработка через:</span>
                    <span className="font-semibold text-foreground">
                      {aiSettings.current_provider}
                    </span>
                    <span className="text-muted-foreground/60">
                      ({aiSettings.current_model})
                    </span>
                  </div>
                </div>
              )}

              {/* Textarea */}
              <div className="relative">
                <Textarea
                  value={rawSummary}
                  onChange={(e) => setRawSummary(e.target.value)}
                  placeholder={"Скопируйте и вставьте сюда текст из Zoom AI Summary...\n\nПоддерживаются форматы:\n— Summary Overview\n— Action Items\n— Decisions & Notes"}
                  rows={14}
                  className="font-mono text-sm rounded-xl border-border/60 bg-background/50 resize-none focus:bg-background placeholder:text-muted-foreground/40"
                />
                {rawSummary && (
                  <div className="absolute bottom-3 right-3 text-2xs text-muted-foreground/50 tabular-nums">
                    {rawSummary.length} символов
                  </div>
                )}
              </div>

              {/* Error */}
              {error && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-destructive/10 text-destructive text-sm">
                  <X className="h-4 w-4 shrink-0" />
                  {error}
                </div>
              )}

              {/* Submit button */}
              <Button
                onClick={handleParse}
                disabled={!rawSummary.trim() || parsing}
                className="w-full h-12 rounded-xl text-base gap-2 bg-accent hover:bg-accent/90 text-accent-foreground shadow-md shadow-accent/20 hover:shadow-lg hover:shadow-accent/25"
              >
                {parsing ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Обработка...
                  </>
                ) : (
                  <>
                    <Search className="h-5 w-5" />
                    Обработать
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ===== PREVIEW STEP ===== */}
      {step === "preview" && parsed && (
        <div className="space-y-5 animate-summary-slide-in">
          {/* Back + header */}
          <div className="flex items-center justify-between">
            <button
              onClick={() => setStep("input")}
              className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground group"
            >
              <ArrowLeft className="h-3.5 w-3.5 group-hover:-translate-x-0.5" />
              Назад к тексту
            </button>
            <Badge variant="secondary" className="gap-1.5 rounded-lg">
              <Sparkles className="h-3 w-3 text-primary" />
              AI результат
            </Badge>
          </div>

          {/* Title + Summary card */}
          <div className="rounded-2xl border border-border/60 bg-card p-6 space-y-4 animate-fade-in-up stagger-1">
            <div>
              <Label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Название встречи
              </Label>
              <Input
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                className="mt-2 h-11 text-base font-heading font-semibold rounded-xl border-border/60"
              />
            </div>
            <div>
              <Label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Краткое резюме
              </Label>
              <Textarea
                value={editSummary}
                onChange={(e) => setEditSummary(e.target.value)}
                rows={3}
                className="mt-2 rounded-xl border-border/60 text-sm"
              />
            </div>
          </div>

          {/* Participants */}
          {editParticipants.length > 0 && (
            <div className="rounded-2xl border border-border/60 bg-card p-5 animate-fade-in-up stagger-2">
              <div className="flex items-center gap-2 mb-3">
                <Users className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Участники
                </span>
                <span className="text-2xs text-muted-foreground/60 ml-auto">
                  {editParticipants.length}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {editParticipants.map((name, i) => (
                  <div
                    key={i}
                    className="inline-flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-muted/60 text-sm"
                  >
                    <UserAvatar name={name} size="sm" />
                    <span className="text-foreground font-medium">{name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Decisions */}
          {editDecisions.length > 0 && (
            <div className="rounded-2xl border border-border/60 bg-card p-5 space-y-3 animate-fade-in-up stagger-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-status-done-fg" />
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Решения
                </span>
                <span className="text-2xs text-muted-foreground/60 ml-auto">
                  {editDecisions.length}
                </span>
              </div>
              <div className="space-y-2">
                {editDecisions.map((decision, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 group"
                  >
                    <span className="flex-shrink-0 h-6 w-6 rounded-lg bg-status-done-bg text-status-done-fg flex items-center justify-center text-xs font-semibold">
                      {i + 1}
                    </span>
                    <Input
                      value={decision}
                      onChange={(e) => {
                        const updated = [...editDecisions];
                        updated[i] = e.target.value;
                        setEditDecisions(updated);
                      }}
                      className="flex-1 h-9 rounded-lg border-border/40 text-sm"
                    />
                    <button
                      onClick={() => removeDecision(i)}
                      className="shrink-0 h-7 w-7 rounded-lg flex items-center justify-center text-muted-foreground/40 hover:text-destructive hover:bg-destructive/10 opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tasks */}
          <div className="rounded-2xl border border-border/60 bg-card p-5 space-y-4 animate-fade-in-up stagger-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ListChecks className="h-4 w-4 text-primary" />
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Задачи
                </span>
                <span className="text-2xs text-muted-foreground/60">
                  {editTasks.length}
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={addTask}
                className="h-8 text-xs gap-1.5 rounded-lg"
              >
                <Plus className="h-3.5 w-3.5" />
                Добавить
              </Button>
            </div>

            {editTasks.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 text-center">
                <div className="h-10 w-10 rounded-xl bg-muted/50 flex items-center justify-center mb-2">
                  <ListChecks className="h-5 w-5 text-muted-foreground/40" />
                </div>
                <p className="text-sm text-muted-foreground">
                  Задачи не найдены в тексте
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={addTask}
                  className="mt-2 text-xs gap-1"
                >
                  <Plus className="h-3.5 w-3.5" />
                  Добавить вручную
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {editTasks.map((task, i) => (
                  <div
                    key={i}
                    className="group relative rounded-xl border border-border/50 bg-background/50 p-4 space-y-3 hover:border-border animate-fade-in-up"
                    style={{ animationDelay: `${i * 40}ms` }}
                  >
                    {/* Task header */}
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-2xs font-mono text-muted-foreground/60 bg-muted/40 rounded px-1.5 py-0.5">
                        #{i + 1}
                      </span>
                      <button
                        onClick={() => removeTask(i)}
                        className="shrink-0 h-7 w-7 rounded-lg flex items-center justify-center text-muted-foreground/40 hover:text-destructive hover:bg-destructive/10 opacity-0 group-hover:opacity-100"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>

                    {/* Task title */}
                    <Input
                      value={task.title}
                      onChange={(e) => updateTask(i, "title", e.target.value)}
                      placeholder="Название задачи"
                      className="h-10 font-medium rounded-lg border-border/40"
                    />

                    {/* Inline fields */}
                    <div className="grid grid-cols-3 gap-2">
                      <div>
                        <Label className="text-2xs text-muted-foreground/70 uppercase tracking-wider">
                          Приоритет
                        </Label>
                        <div className="flex gap-1 mt-1.5">
                          {(["low", "medium", "high", "urgent"] as TaskPriority[]).map((p) => (
                            <button
                              key={p}
                              onClick={() => updateTask(i, "priority", p)}
                              className={`
                                flex-1 h-8 rounded-lg text-2xs font-semibold border
                                ${
                                  task.priority === p
                                    ? PRIORITY_COLORS[p]
                                    : "border-border/40 text-muted-foreground/50 hover:border-border"
                                }
                              `}
                            >
                              {PRIORITY_LABELS[p].slice(0, 3)}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div>
                        <Label className="text-2xs text-muted-foreground/70 uppercase tracking-wider">
                          Исполнитель
                        </Label>
                        <Input
                          value={task.assignee_name || ""}
                          onChange={(e) =>
                            updateTask(i, "assignee_name", e.target.value || null)
                          }
                          placeholder="Имя"
                          className="mt-1.5 h-8 text-sm rounded-lg border-border/40"
                        />
                      </div>

                      <div>
                        <Label className="text-2xs text-muted-foreground/70 uppercase tracking-wider">
                          Дедлайн
                        </Label>
                        <Input
                          type="date"
                          value={task.deadline || ""}
                          onChange={(e) =>
                            updateTask(i, "deadline", e.target.value || null)
                          }
                          className="mt-1.5 h-8 text-sm rounded-lg border-border/40"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-destructive/10 text-destructive text-sm">
              <X className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2 pb-4 sticky bottom-0 bg-gradient-to-t from-background via-background to-transparent">
            <Button
              onClick={handleCreate}
              disabled={creating || !editTitle.trim()}
              className="flex-1 h-12 rounded-xl text-base gap-2 bg-primary hover:bg-primary/90 text-primary-foreground shadow-md shadow-primary/20"
            >
              {creating ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Создание...
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-5 w-5" />
                  Создать встречу и {editTasks.length} задач
                </>
              )}
            </Button>
            <Button
              variant="outline"
              onClick={() => setStep("input")}
              disabled={creating}
              className="h-12 px-6 rounded-xl"
            >
              Отмена
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
