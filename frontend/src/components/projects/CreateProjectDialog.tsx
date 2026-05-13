"use client";

import { useState, type FormEvent } from "react";
import { Check, Loader2, Plus, X } from "lucide-react";
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
import type { Department, Project, TeamMember } from "@/lib/types";

export function CreateProjectDialog({
  open,
  onOpenChange,
  members,
  departments,
  onCreated,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  members: TeamMember[];
  departments: Department[];
  onCreated: (project: Project) => void | Promise<void>;
}) {
  const { toastSuccess, toastError } = useToast();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [ownerId, setOwnerId] = useState("");
  const [departmentIds, setDepartmentIds] = useState<string[]>([]);
  const [milestoneTitles, setMilestoneTitles] = useState([""]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const activeMembers = members.filter((member) => member.is_active);
  const activeDepartments = departments.filter((department) => department.is_active);

  function resetForm() {
    setTitle("");
    setDescription("");
    setOwnerId("");
    setDepartmentIds([]);
    setMilestoneTitles([""]);
    setError(null);
  }

  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen && !saving) resetForm();
    onOpenChange(nextOpen);
  }

  function toggleDepartment(departmentId: string) {
    setDepartmentIds((current) =>
      current.includes(departmentId)
        ? current.filter((id) => id !== departmentId)
        : [...current, departmentId],
    );
  }

  function updateMilestoneTitle(index: number, value: string) {
    setMilestoneTitles((current) =>
      current.map((milestone, currentIndex) =>
        currentIndex === index ? value : milestone,
      ),
    );
  }

  function addMilestoneRow() {
    setMilestoneTitles((current) => [...current, ""]);
  }

  function removeMilestoneRow(index: number) {
    setMilestoneTitles((current) => {
      const next = current.filter((_, currentIndex) => currentIndex !== index);
      return next.length > 0 ? next : [""];
    });
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

    const initialMilestones = milestoneTitles
      .map((milestoneTitle) => milestoneTitle.trim())
      .filter(Boolean);

    setSaving(true);
    setError(null);
    try {
      let project = await api.createProject({
        title: trimmedTitle,
        description: trimmedDescription,
        owner_id: ownerId,
        department_ids: departmentIds,
      });

      let milestoneError = false;
      for (const milestoneTitle of initialMilestones) {
        try {
          project = await api.addProjectMilestone(project.id, {
            title: milestoneTitle,
          });
        } catch {
          milestoneError = true;
        }
      }

      resetForm();
      onOpenChange(false);
      await onCreated(project);

      if (milestoneError) {
        toastError("Проект создан, но часть этапов не добавлена");
      } else {
        toastSuccess("Проект создан");
      }
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
          <DialogTitle className="text-lg">Новый проект</DialogTitle>
          <DialogDescription>
            Создайте проект напрямую, назначьте владельца и начальные этапы.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div className="space-y-2">
            <Label htmlFor="project-title">Название</Label>
            <Input
              id="project-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Коротко сформулируйте проект"
              className="h-9 border-border/70 bg-muted/20"
              disabled={saving}
              autoFocus
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="project-description">Описание</Label>
            <Textarea
              id="project-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Цель, ожидаемый результат, важный контекст"
              rows={4}
              className="min-h-[108px] resize-none border-border/70 bg-muted/20"
              disabled={saving}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="project-owner">Владелец проекта</Label>
            <Select
              value={ownerId || undefined}
              onValueChange={setOwnerId}
              disabled={saving}
            >
              <SelectTrigger
                id="project-owner"
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
            <Label>Вовлечённые отделы</Label>
            <div className="max-h-36 space-y-1 overflow-y-auto rounded-md border border-border/70 bg-muted/10 p-2">
              {activeDepartments.length === 0 ? (
                <p className="px-1 py-2 text-sm text-muted-foreground">
                  Активные отделы не найдены
                </p>
              ) : (
                activeDepartments.map((department) => {
                  const checked = departmentIds.includes(department.id);

                  return (
                    <button
                      key={department.id}
                      type="button"
                      role="checkbox"
                      aria-checked={checked}
                      disabled={saving}
                      onClick={() => toggleDepartment(department.id)}
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
                      <span className="min-w-0 truncate">{department.name}</span>
                    </button>
                  );
                })
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              Необязательно. Для выбранных отделов владельцем станет владелец проекта.
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between gap-3">
              <Label>Начальные этапы</Label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={addMilestoneRow}
                disabled={saving}
                className="h-7 gap-1.5 rounded-md px-2 text-xs"
              >
                <Plus className="h-3.5 w-3.5" />
                Добавить
              </Button>
            </div>
            <div className="space-y-1.5">
              {milestoneTitles.map((milestoneTitle, index) => (
                <div key={index} className="flex min-w-0 items-center gap-2">
                  <Input
                    value={milestoneTitle}
                    onChange={(event) =>
                      updateMilestoneTitle(index, event.target.value)
                    }
                    placeholder={`Этап ${index + 1}`}
                    className="h-8 min-w-0 border-border/70 bg-muted/20 text-sm"
                    disabled={saving}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => removeMilestoneRow(index)}
                    disabled={saving || milestoneTitles.length === 1}
                    aria-label="Удалить этап"
                    className="h-8 w-8 shrink-0 text-muted-foreground hover:text-destructive"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">
              Пустые строки будут пропущены.
            </p>
          </div>

          {error && (
            <p className="rounded-md border border-destructive/25 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}

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
              {saving && <Loader2 className="h-4 w-4 animate-spin" />}
              Создать проект
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
