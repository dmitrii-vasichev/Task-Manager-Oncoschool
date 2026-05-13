"use client";

import { useState, type FormEvent } from "react";
import { Loader2 } from "lucide-react";
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
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/shared/Toast";
import { api } from "@/lib/api";
import type { Idea, TeamMember } from "@/lib/types";

const SELECT_CLASS =
  "h-9 w-full rounded-md border border-border/70 bg-background px-3 text-sm text-foreground shadow-sm outline-none transition-colors hover:border-primary/30 focus:border-primary/40 focus:ring-1 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-60";

export function CreateIdeaDialog({
  open,
  onOpenChange,
  members,
  onCreated,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  members: TeamMember[];
  onCreated: (idea: Idea) => void;
}) {
  const { toastSuccess, toastError } = useToast();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [reviewOwnerId, setReviewOwnerId] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function resetForm() {
    setTitle("");
    setDescription("");
    setReviewOwnerId("");
    setError(null);
  }

  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen && !saving) resetForm();
    onOpenChange(nextOpen);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    const trimmedTitle = title.trim();
    const trimmedDescription = description.trim();
    if (!trimmedTitle) {
      setError("Введите название идеи");
      return;
    }
    if (!trimmedDescription) {
      setError("Добавьте описание идеи");
      return;
    }
    if (!reviewOwnerId) {
      setError("Выберите ответственного за рассмотрение");
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const idea = await api.createIdea({
        title: trimmedTitle,
        description: trimmedDescription,
        review_owner_id: reviewOwnerId,
      });
      resetForm();
      onCreated(idea);
      onOpenChange(false);
      toastSuccess("Идея создана");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Не удалось создать идею";
      setError(message);
      toastError(message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={handleOpenChange}
    >
      <DialogContent className="max-h-[calc(100vh-1.5rem)] overflow-y-auto sm:max-w-[520px]">
        <DialogHeader>
          <DialogTitle className="text-lg">Новая идея</DialogTitle>
          <DialogDescription>
            Зафиксируйте предложение и назначьте ответственного за review.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div className="space-y-2">
            <Label htmlFor="idea-title">Название</Label>
            <Input
              id="idea-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Коротко сформулируйте идею"
              className="h-9 border-border/70 bg-muted/20"
              disabled={saving}
              autoFocus
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="idea-description">Описание</Label>
            <Textarea
              id="idea-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Проблема, ожидаемый результат, важные детали"
              rows={4}
              className="min-h-[108px] resize-none border-border/70 bg-muted/20"
              disabled={saving}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="idea-review-owner">Ответственный за review</Label>
            <select
              id="idea-review-owner"
              value={reviewOwnerId || "all"}
              onChange={(event) =>
                setReviewOwnerId(event.target.value === "all" ? "" : event.target.value)
              }
              className={SELECT_CLASS}
              disabled={saving}
            >
              <option value="all">Выберите участника</option>
              {members.map((member) => (
                <option key={member.id} value={member.id}>
                  {member.full_name}
                </option>
              ))}
            </select>
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
              Создать идею
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
