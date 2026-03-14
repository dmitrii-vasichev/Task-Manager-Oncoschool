"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Users } from "lucide-react";
import { MemberCard } from "./MemberCard";
import type { DepartmentWithMembers, TeamMember } from "@/lib/types";

interface DepartmentNodeProps {
  department: DepartmentWithMembers;
  onMemberClick: (member: TeamMember) => void;
  onMemberEdit?: (member: TeamMember) => void;
  canEdit: boolean;
  defaultExpanded?: boolean;
}

export function DepartmentNode({
  department,
  onMemberClick,
  onMemberEdit,
  canEdit,
  defaultExpanded = true,
}: DepartmentNodeProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  const activeMembers = department.members.filter((m) => m.is_active);
  const inactiveMembers = department.members.filter((m) => !m.is_active);
  const sortedMembers = [...activeMembers, ...inactiveMembers];

  return (
    <div className="rounded-2xl border border-border/60 bg-card overflow-hidden">
      {/* Header */}
      <button
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-muted/30 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div
          className="w-1 h-8 rounded-full shrink-0"
          style={{ backgroundColor: department.color || "#6B7280" }}
        />
        {expanded ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
        )}
        <span className="font-heading font-semibold text-sm">
          {department.name}
        </span>
        <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-2xs font-medium bg-muted text-muted-foreground">
          <Users className="h-3 w-3" />
          {department.members.length}
        </span>
        {department.description && (
          <span className="hidden sm:inline text-xs text-muted-foreground truncate ml-auto mr-2">
            {department.description}
          </span>
        )}
      </button>

      {/* Members grid */}
      {expanded && (
        <div className="px-4 pb-4 pt-1">
          {sortedMembers.length === 0 ? (
            <p className="text-sm text-muted-foreground/60 py-4 text-center">
              Нет участников
            </p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {sortedMembers.map((member) => (
                <MemberCard
                  key={member.id}
                  member={member}
                  isHead={department.head_id === member.id}
                  onClick={() => onMemberClick(member)}
                  onEdit={canEdit ? () => onMemberEdit?.(member) : undefined}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
