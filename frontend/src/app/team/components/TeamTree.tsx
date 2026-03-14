"use client";

import { DepartmentNode } from "./DepartmentNode";
import type { TeamTreeResponse, TeamMember, DepartmentWithMembers } from "@/lib/types";

interface TeamTreeProps {
  tree: TeamTreeResponse;
  onMemberClick: (member: TeamMember) => void;
  onMemberEdit?: (member: TeamMember) => void;
  canEdit: boolean;
}

export function TeamTree({ tree, onMemberClick, onMemberEdit, canEdit }: TeamTreeProps) {
  const unassignedDept: DepartmentWithMembers = {
    id: "__unassigned__",
    name: "Без отдела",
    description: null,
    head_id: null,
    color: "#6B7280",
    sort_order: 9999,
    is_active: true,
    created_at: "",
    members: tree.unassigned,
  };

  const hasUnassigned = tree.unassigned.length > 0;

  return (
    <div className="space-y-2">
      {tree.departments.map((dept, i) => (
        <div
          key={dept.id}
          className="animate-fade-in-up"
          style={{ animationDelay: `${i * 60}ms` }}
        >
          <DepartmentNode
            department={dept}
            onMemberClick={onMemberClick}
            onMemberEdit={onMemberEdit}
            canEdit={canEdit}
          />
        </div>
      ))}
      {hasUnassigned && (
        <div
          className="animate-fade-in-up"
          style={{ animationDelay: `${tree.departments.length * 60}ms` }}
        >
          <DepartmentNode
            department={unassignedDept}
            onMemberClick={onMemberClick}
            onMemberEdit={onMemberEdit}
            canEdit={canEdit}
            defaultExpanded={tree.departments.length === 0}
          />
        </div>
      )}
    </div>
  );
}
