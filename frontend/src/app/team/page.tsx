"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Pencil,
  Loader2,
  X,
  Plus,
  Users,
  CheckCircle2,
  ListTodo,
  AlertTriangle,
  Search,
} from "lucide-react";
import { ModeratorGuard } from "@/components/shared/ModeratorGuard";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { RoleBadge } from "@/components/shared/RoleBadge";
import { UserAvatar } from "@/components/shared/UserAvatar";
import { useTeam } from "@/hooks/useTeam";
import { api } from "@/lib/api";
import type { TeamMember, MemberRole, MemberStats } from "@/lib/types";
import { EmptyState } from "@/components/shared/EmptyState";
import { useToast } from "@/components/shared/Toast";

export default function TeamPage() {
  return (
    <ModeratorGuard>
      <TeamContent />
    </ModeratorGuard>
  );
}

function TeamContent() {
  const { toastSuccess, toastError } = useToast();
  const { members, loading, refetch } = useTeam();
  const [memberStats, setMemberStats] = useState<Record<string, MemberStats>>(
    {}
  );
  const [editMember, setEditMember] = useState<TeamMember | null>(null);
  const [editFullName, setEditFullName] = useState("");
  const [editRole, setEditRole] = useState<MemberRole>("member");
  const [editNameVariants, setEditNameVariants] = useState<string[]>([]);
  const [editActive, setEditActive] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newVariant, setNewVariant] = useState("");
  const [search, setSearch] = useState("");

  const fetchStats = useCallback(async () => {
    try {
      const data = await api.getMembersAnalytics();
      const map: Record<string, MemberStats> = {};
      data.members.forEach((m) => {
        map[m.id] = m;
      });
      setMemberStats(map);
    } catch {
      // stats are optional enhancement
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const openEdit = (member: TeamMember) => {
    setEditMember(member);
    setEditFullName(member.full_name);
    setEditRole(member.role);
    setEditNameVariants([...member.name_variants]);
    setEditActive(member.is_active);
    setError(null);
    setNewVariant("");
  };

  const handleSave = async () => {
    if (!editMember) return;
    setSaving(true);
    setError(null);
    try {
      await api.updateTeamMember(editMember.id, {
        full_name: editFullName,
        role: editRole,
        name_variants: editNameVariants,
        is_active: editActive,
      });
      setEditMember(null);
      refetch();
      fetchStats();
      toastSuccess("Участник обновлён");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Ошибка сохранения";
      setError(msg);
      toastError(msg);
    } finally {
      setSaving(false);
    }
  };

  const addVariant = () => {
    const trimmed = newVariant.trim();
    if (trimmed && !editNameVariants.includes(trimmed)) {
      setEditNameVariants((prev) => [...prev, trimmed]);
      setNewVariant("");
    }
  };

  const removeVariant = (index: number) => {
    setEditNameVariants((prev) => prev.filter((_, i) => i !== index));
  };

  const filtered = members.filter((m) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      m.full_name.toLowerCase().includes(q) ||
      m.telegram_username?.toLowerCase().includes(q) ||
      m.name_variants.some((v) => v.toLowerCase().includes(q))
    );
  });

  const activeCount = members.filter((m) => m.is_active).length;
  const moderatorCount = members.filter((m) => m.role === "moderator").length;

  if (loading) {
    return (
      <div className="space-y-6 animate-in fade-in duration-300">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-48 rounded-xl" />
          <Skeleton className="h-10 w-72 rounded-xl" />
        </div>
        <div className="grid gap-3">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-2xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header stats */}
      <div className="flex flex-wrap items-center gap-3 animate-fade-in-up stagger-1">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
            <Users className="h-4 w-4 text-primary" />
          </div>
          <span>
            <span className="font-heading font-bold text-foreground text-lg">
              {members.length}
            </span>{" "}
            участников
          </span>
        </div>
        <div className="h-4 w-px bg-border/60" />
        <span className="text-xs text-muted-foreground">
          Активных: {activeCount}
        </span>
        <div className="h-4 w-px bg-border/60" />
        <span className="text-xs text-muted-foreground">
          Модераторов: {moderatorCount}
        </span>
      </div>

      {/* Search */}
      <div className="relative max-w-sm animate-fade-in-up stagger-2">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Поиск по имени или username..."
          className="pl-9 h-10 rounded-xl bg-card border-border/60"
        />
      </div>

      {/* Members grid */}
      {filtered.length === 0 ? (
        <EmptyState
          variant="team"
          title={search ? "Никто не найден" : "В команде пока нет участников"}
          description={
            search
              ? "Попробуйте изменить поисковый запрос"
              : "Участники появятся, когда напишут боту /start в Telegram"
          }
        />
      ) : (
        <div className="grid gap-3">
          {filtered.map((member, i) => {
            const stats = memberStats[member.id];
            return (
              <div
                key={member.id}
                className={`
                  group relative overflow-hidden rounded-2xl border border-border/60 bg-card p-5
                  hover:shadow-lg hover:shadow-primary/5 hover:-translate-y-0.5
                  animate-fade-in-up stagger-${Math.min(i + 3, 8)}
                  ${!member.is_active ? "opacity-60" : ""}
                `}
              >
                {/* Decorative accent */}
                <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-primary/[0.03] to-transparent rounded-bl-3xl" />

                <div className="flex items-center gap-4">
                  {/* Avatar */}
                  <UserAvatar name={member.full_name} size="lg" />

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-heading font-semibold text-[15px] truncate">
                        {member.full_name}
                      </span>
                      <RoleBadge role={member.role} />
                      {!member.is_active && (
                        <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-2xs font-medium bg-muted text-muted-foreground ring-1 ring-inset ring-border/60">
                          Неактивен
                        </span>
                      )}
                    </div>

                    {member.telegram_username && (
                      <p className="text-sm text-muted-foreground mt-0.5">
                        @{member.telegram_username}
                      </p>
                    )}

                    {/* Name variants */}
                    {member.name_variants.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {member.name_variants.map((v, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center rounded-md px-1.5 py-0.5 text-2xs font-medium bg-secondary text-secondary-foreground"
                          >
                            {v}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Stats — desktop: full layout */}
                  {stats && (
                    <div className="hidden sm:flex items-center gap-3 shrink-0">
                      <div className="text-center min-w-[48px]">
                        <div className="flex items-center justify-center gap-1 text-xs text-muted-foreground mb-0.5">
                          <ListTodo className="h-3 w-3" />
                        </div>
                        <span className="font-heading font-bold text-sm">
                          {stats.tasks_in_progress}
                        </span>
                        <p className="text-2xs text-muted-foreground">
                          активных
                        </p>
                      </div>
                      <div className="h-8 w-px bg-border/60" />
                      <div className="text-center min-w-[48px]">
                        <div className="flex items-center justify-center gap-1 text-xs text-status-done-fg mb-0.5">
                          <CheckCircle2 className="h-3 w-3" />
                        </div>
                        <span className="font-heading font-bold text-sm text-status-done-fg">
                          {stats.tasks_done}
                        </span>
                        <p className="text-2xs text-muted-foreground">
                          выполнено
                        </p>
                      </div>
                      {stats.tasks_overdue > 0 && (
                        <>
                          <div className="h-8 w-px bg-border/60" />
                          <div className="text-center min-w-[48px]">
                            <div className="flex items-center justify-center gap-1 text-xs text-destructive mb-0.5">
                              <AlertTriangle className="h-3 w-3" />
                            </div>
                            <span className="font-heading font-bold text-sm text-destructive">
                              {stats.tasks_overdue}
                            </span>
                            <p className="text-2xs text-muted-foreground">
                              просрочено
                            </p>
                          </div>
                        </>
                      )}
                    </div>
                  )}

                  {/* Stats — mobile: compact badges */}
                  {stats && (
                    <div className="flex sm:hidden items-center gap-1.5 shrink-0">
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-muted text-2xs font-medium text-muted-foreground">
                        <ListTodo className="h-2.5 w-2.5" />
                        {stats.tasks_in_progress}
                      </span>
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-status-done-bg text-2xs font-medium text-status-done-fg">
                        <CheckCircle2 className="h-2.5 w-2.5" />
                        {stats.tasks_done}
                      </span>
                      {stats.tasks_overdue > 0 && (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-destructive/10 text-2xs font-medium text-destructive">
                          {stats.tasks_overdue}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Edit button */}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="shrink-0 h-9 w-9 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted opacity-0 group-hover:opacity-100"
                    onClick={() => openEdit(member)}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Edit Dialog */}
      <Dialog
        open={!!editMember}
        onOpenChange={(open) => !open && setEditMember(null)}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3 font-heading">
              {editMember && (
                <UserAvatar name={editMember.full_name} size="default" />
              )}
              Редактировать участника
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-5 pt-2">
            <div>
              <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Полное имя
              </Label>
              <Input
                value={editFullName}
                onChange={(e) => setEditFullName(e.target.value)}
                className="mt-1.5 rounded-xl"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Роль
                </Label>
                <Select
                  value={editRole}
                  onValueChange={(v) => setEditRole(v as MemberRole)}
                >
                  <SelectTrigger className="mt-1.5 rounded-xl">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="moderator">Модератор</SelectItem>
                    <SelectItem value="member">Участник</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Статус
                </Label>
                <Select
                  value={editActive ? "active" : "inactive"}
                  onValueChange={(v) => setEditActive(v === "active")}
                >
                  <SelectTrigger className="mt-1.5 rounded-xl">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Активен</SelectItem>
                    <SelectItem value="inactive">Неактивен</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Варианты имени (для AI-матчинга)
              </Label>
              <div className="flex flex-wrap gap-1.5 mt-2 min-h-[32px]">
                {editNameVariants.map((v, i) => (
                  <Badge
                    key={i}
                    variant="secondary"
                    className="cursor-pointer rounded-lg gap-1 hover:bg-destructive/10 hover:text-destructive group/chip"
                    onClick={() => removeVariant(i)}
                  >
                    {v}
                    <X className="h-3 w-3 opacity-50 group-hover/chip:opacity-100" />
                  </Badge>
                ))}
                {editNameVariants.length === 0 && (
                  <span className="text-xs text-muted-foreground/60 self-center">
                    Нет вариантов
                  </span>
                )}
              </div>
              <div className="flex gap-2 mt-2">
                <Input
                  value={newVariant}
                  onChange={(e) => setNewVariant(e.target.value)}
                  placeholder="Добавить вариант..."
                  className="rounded-xl"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addVariant();
                    }
                  }}
                />
                <Button
                  variant="outline"
                  size="icon"
                  className="shrink-0 rounded-xl"
                  onClick={addVariant}
                  disabled={!newVariant.trim()}
                >
                  <Plus className="h-4 w-4" />
                </Button>
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
                onClick={() => setEditMember(null)}
                disabled={saving}
              >
                Отмена
              </Button>
              <Button
                className="rounded-xl"
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Сохранение...
                  </>
                ) : (
                  "Сохранить"
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
