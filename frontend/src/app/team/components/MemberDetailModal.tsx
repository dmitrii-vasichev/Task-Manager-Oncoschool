"use client";

import { Mail, Send, Calendar, Building2, Users, Tag } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { RoleBadge } from "@/components/shared/RoleBadge";
import { UserAvatar } from "@/components/shared/UserAvatar";
import type { TeamMember, Department, MemberStats } from "@/lib/types";

interface MemberDetailModalProps {
  member: TeamMember | null;
  stats?: MemberStats;
  departments: Department[];
  onClose: () => void;
}

function formatBirthday(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" });
}

function formatJoinDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("ru-RU", { month: "long", year: "numeric" });
}

export function MemberDetailModal({ member, stats, departments, onClose }: MemberDetailModalProps) {
  if (!member) return null;

  const dept = departments.find((d) => d.id === member.department_id);
  const extraDepartments = departments.filter(
    (d) =>
      (member.extra_department_ids || []).includes(d.id) &&
      d.id !== member.department_id
  );

  return (
    <Dialog open={!!member} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="sr-only">
            {member.full_name}
          </DialogTitle>
        </DialogHeader>

        <div className="flex flex-col sm:flex-row gap-6">
          {/* Left: Avatar & basic info */}
          <div className="flex flex-col items-center sm:items-start gap-3 sm:w-1/3 shrink-0">
            <UserAvatar
              name={member.full_name}
              avatarUrl={member.avatar_url}
              size="xl"
            />
            <div className="text-center sm:text-left">
              <h3 className="font-heading font-semibold text-lg leading-tight">
                {member.full_name}
              </h3>
              {member.position && (
                <p className="text-sm text-muted-foreground mt-0.5">
                  {member.position}
                </p>
              )}
              <div className="mt-2">
                <RoleBadge role={member.role} />
              </div>
              {!member.is_active && (
                <span className="inline-flex items-center mt-1.5 rounded-full px-2 py-0.5 text-2xs font-medium bg-muted text-muted-foreground ring-1 ring-inset ring-border/60">
                  Неактивен
                </span>
              )}
            </div>
          </div>

          {/* Right: Details */}
          <div className="flex-1 space-y-4 min-w-0">
            {/* Contacts */}
            {(member.email || member.telegram_username) && (
              <section>
                <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                  Контакты
                </h4>
                <div className="space-y-1.5">
                  {member.email && (
                    <a
                      href={`mailto:${member.email}`}
                      className="flex items-center gap-2 text-sm text-primary hover:underline"
                    >
                      <Mail className="h-3.5 w-3.5 shrink-0" />
                      {member.email}
                    </a>
                  )}
                  {member.telegram_username && (
                    <a
                      href={`https://t.me/${member.telegram_username}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm text-primary hover:underline"
                    >
                      <Send className="h-3.5 w-3.5 shrink-0" />
                      @{member.telegram_username}
                    </a>
                  )}
                </div>
              </section>
            )}

            {/* Info */}
            <section>
              <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                Информация
              </h4>
              <div className="space-y-1.5">
                {dept && (
                  <div className="flex items-center gap-2 text-sm">
                    <Building2 className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                    <span
                      className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium"
                      style={{
                        backgroundColor: dept.color ? `${dept.color}18` : undefined,
                        color: dept.color || undefined,
                      }}
                    >
                      <span
                        className="h-2 w-2 rounded-full shrink-0"
                        style={{ backgroundColor: dept.color || "#6B7280" }}
                      />
                      {dept.name}
                    </span>
                  </div>
                )}
                {extraDepartments.length > 0 && (
                  <div className="flex items-start gap-2 text-sm">
                    <Building2 className="h-3.5 w-3.5 text-muted-foreground shrink-0 mt-0.5" />
                    <div className="flex flex-wrap gap-1.5">
                      {extraDepartments.map((extraDept) => (
                        <span
                          key={extraDept.id}
                          className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium"
                          style={{
                            backgroundColor: extraDept.color
                              ? `${extraDept.color}18`
                              : undefined,
                            color: extraDept.color || undefined,
                          }}
                        >
                          <span
                            className="h-2 w-2 rounded-full shrink-0"
                            style={{
                              backgroundColor: extraDept.color || "#6B7280",
                            }}
                          />
                          {extraDept.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {member.birthday && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Calendar className="h-3.5 w-3.5 shrink-0" />
                    {formatBirthday(member.birthday)}
                  </div>
                )}
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Users className="h-3.5 w-3.5 shrink-0" />
                  В команде с {formatJoinDate(member.created_at)}
                </div>
              </div>
            </section>

            {/* Stats */}
            {stats && (
              <section>
                <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                  Статистика задач
                </h4>
                <div className="grid grid-cols-3 gap-2">
                  <div className="rounded-xl bg-muted/50 p-2.5 text-center">
                    <span className="font-heading font-bold text-lg">{stats.tasks_in_progress}</span>
                    <p className="text-2xs text-muted-foreground">В работе</p>
                  </div>
                  <div className="rounded-xl bg-status-done-bg p-2.5 text-center">
                    <span className="font-heading font-bold text-lg text-status-done-fg">{stats.tasks_done}</span>
                    <p className="text-2xs text-muted-foreground">Выполнено</p>
                  </div>
                  <div className="rounded-xl bg-muted/50 p-2.5 text-center">
                    <span className="font-heading font-bold text-lg">{stats.total_tasks}</span>
                    <p className="text-2xs text-muted-foreground">Всего</p>
                  </div>
                </div>
              </section>
            )}

            {/* Name variants */}
            {member.name_variants.length > 0 && (
              <section>
                <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                  Варианты имени
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {member.name_variants.map((v, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-2xs font-medium bg-secondary text-secondary-foreground"
                    >
                      <Tag className="h-2.5 w-2.5" />
                      {v}
                    </span>
                  ))}
                </div>
              </section>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
