"use client";

import { useEffect, useState, type FormEvent } from "react";
import { Check, Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/shared/Toast";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Idea, Project, TeamMember } from "@/lib/types";

interface CreateProjectFromIdeaDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  idea: Idea;
  members: TeamMember[];
  onCreated: (project: Project) => void;
}

export function CreateProjectFromIdeaDialog({
  open,
  onOpenChange,
  idea,
  members,
  onCreated,
}: CreateProjectFromIdeaDialogProps) {
  const { toastSuccess, toastError } = useToast();
  const [title, setTitle] = useState(idea.title);
  const [description, setDescription] = useState(idea.description);
  const [ownerId, setOwnerId] = useState(idea.review_owner_id);
  const [departmentIds, setDepartmentIds] = useState<string[]>(
    idea.departments.map((department) => department.department_id),
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const activeMembers = members.filter((member) => member.is_active);
  const ideaDepartments = idea.departments.filter((department) => department.department);

  useEffect(() => {
    if (!open) return;
    setTitle(idea.title);
    setDescription(idea.description);
    setOwnerId(idea.review_owner_id);
    setDepartmentIds(idea.departments.map((department) => department.department_id));
    setError(null);
  }, [idea, open]);

  function handleOpenChange(nextOpen: boolean) {
    if (!saving) onOpenChange(nextOpen);
  }

  function toggleDepartment(departmentId: string) {
    setDepartmentIds((current) =>
      current.includes(departmentId)
        ? current.filter((id) => id !== departmentId)
        : [...current, departmentId],
    );
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    const trimmedTitle = title.trim();
    const trimmedDescription = description.trim();
    if (!trimmedTitle) {
      setError("Введите название проекта");
      return;
    }
    if (!trimmedDescription) {
      setError("Добавьте описание проекта");
      return;
    }
    if (!ownerId) {
      setError("Выберите владельца проекта");
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const project = await api.createProject({
        title: trimmedTitle,
        description: trimmedDescription,
        owner_id: ownerId,
        source_idea_id: idea.id,
        department_ids: departmentIds,
      });
      onCreated(project);
      onOpenChange(false);
      toastSuccess("Проект создан");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Не удалось создать проект";
      setError(message);
      toastError(message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-h-[calc(100vh-1.5rem)] overflow-y-auto sm:max-w-[560px]">
        <DialogHeader>
          <DialogTitle className="text-lg">Проект по идее</DialogTitle>
          <DialogDescription>
            Создайте проект из принятой идеи и сохраните связь с исходной карточкой.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div className="space-y-2">
            <Label htmlFor="idea-project-title">Название</Label>
            <Input
              id="idea-project-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Название проекта"
              className="h-9 border-border/70 bg-muted/20"
              disabled={saving}
              autoFocus
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="idea-project-description">Описание</Label>
            <Textarea
              id="idea-project-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Цель, ожидаемый результат, важный контекст"
              rows={4}
              className="min-h-[108px] resize-none border-border/70 bg-muted/20"
              disabled={saving}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="idea-project-owner">Владелец проекта</Label>
            <Select
              value={ownerId || undefined}
              onValueChange={setOwnerId}
              disabled={saving}
            >
              <SelectTrigger
                id="idea-project-owner"
                className="h-9 border-border/70 bg-muted/20 text-sm shadow-sm transition-colors hover:border-primary/30 focus:border-primary/40 focus:ring-primary/20"
              >
                <SelectValue placeholder="Выберите участника" />
              </SelectTrigger>
              <SelectContent className="z-[70] max-h-72 border-border/70 shadow-xl">
                {activeMembers.map((member) => (
                  <SelectItem key={member.id} value={member.id}>
                    {member.full_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Отделы из идеи</Label>
            <div className="max-h-36 space-y-1 overflow-y-auto rounded-md border border-border/70 bg-muted/10 p-2">
              {ideaDepartments.length === 0 ? (
                <p className="px-1 py-2 text-sm text-muted-foreground">
                  В идее нет выбранных отделов
                </p>
              ) : (
                ideaDepartments.map((department) => {
                  const checked = departmentIds.includes(department.department_id);

                  return (
                    <button
                      key={department.id}
                      type="button"
                      role="checkbox"
                      aria-checked={checked}
                      disabled={saving}
                      onClick={() => toggleDepartment(department.department_id)}
                      className={cn(
                        "flex w-full min-w-0 items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors",
                        "hover:bg-background/70 focus:outline-none focus:ring-1 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-60",
                        checked && "bg-primary/10 text-foreground",
                      )}
                    >
                      <span
                        className={cn(
                          "flex h-4 w-4 shrink-0 items-center justify-center rounded border transition-colors",
                          checked
                            ? "border-primary bg-primary text-primary-foreground"
                            : "border-border/80 bg-background text-transparent",
                        )}
                      >
                        <Check className="h-3 w-3" strokeWidth={3} />
                      </span>
                      <span className="min-w-0 truncate">
                        {department.department?.name || "Отдел не указан"}
                      </span>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {error ? (
            <p className="rounded-md border border-destructive/25 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          ) : null}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={saving}
            >
              Отмена
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              Создать проект
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
