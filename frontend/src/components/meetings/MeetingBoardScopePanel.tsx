"use client";

import { Building2, Pin, UserPlus, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Department, MeetingBoardSettings, TeamMember } from "@/lib/types";

interface MeetingBoardScopePanelProps {
  settings: MeetingBoardSettings;
  members: TeamMember[];
  departments: Department[];
  isModerator: boolean;
}

export function MeetingBoardScopePanel({
  settings,
  members,
  departments,
  isModerator,
}: MeetingBoardScopePanelProps) {
  const addedMemberCount = settings.added_member_ids.filter((id) =>
    members.some((member) => member.id === id)
  ).length;
  const addedDepartmentCount = settings.added_department_ids.filter((id) =>
    departments.some((department) => department.id === id)
  ).length;

  const stats = [
    {
      label: "Люди",
      value: addedMemberCount,
      icon: Users,
    },
    {
      label: "Отделы",
      value: addedDepartmentCount,
      icon: Building2,
    },
    {
      label: "Закреплено",
      value: settings.pinned_task_ids.length,
      icon: Pin,
    },
  ];

  return (
    <aside className="rounded-xl border border-border/70 bg-card p-4">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-heading font-semibold text-foreground">
            Область доски
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Дополнительные участники и фокус встречи
          </p>
        </div>

        {isModerator && (
          <Button variant="outline" size="sm" className="rounded-lg">
            <UserPlus className="h-3.5 w-3.5" />
            Добавить
          </Button>
        )}
      </div>

      <div className="grid grid-cols-3 gap-2">
        {stats.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.label}
              className="rounded-lg border border-border/60 bg-background/60 p-2.5"
            >
              <div className="mb-2 flex items-center justify-between gap-2">
                <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-base font-heading font-semibold text-foreground">
                  {item.value}
                </span>
              </div>
              <p className="truncate text-2xs text-muted-foreground">{item.label}</p>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
