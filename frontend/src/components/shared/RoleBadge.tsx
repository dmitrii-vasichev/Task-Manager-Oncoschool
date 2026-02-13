import type { MemberRole } from "@/lib/types";
import { Crown, Shield, User } from "lucide-react";

const ROLE_CONFIG: Record<
  MemberRole,
  { label: string; icon: typeof Shield; className: string }
> = {
  admin: {
    label: "Администратор",
    icon: Crown,
    className:
      "bg-role-admin-bg text-role-admin-fg ring-1 ring-inset ring-role-admin-ring",
  },
  moderator: {
    label: "Модератор",
    icon: Shield,
    className:
      "bg-role-moderator-bg text-role-moderator-fg ring-1 ring-inset ring-role-moderator-ring",
  },
  member: {
    label: "Участник",
    icon: User,
    className:
      "bg-role-member-bg text-role-member-fg ring-1 ring-inset ring-role-member-ring",
  },
};

export function RoleBadge({ role }: { role: MemberRole }) {
  const { label, icon: Icon, className } = ROLE_CONFIG[role];

  return (
    <span
      className={`badge-animated inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${className}`}
    >
      <Icon className="h-3 w-3 shrink-0" />
      {label}
    </span>
  );
}
